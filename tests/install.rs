//! `install.sh` is the one command a person runs. This publishes the built binary as a
//! release would (a tarball and its checksum per platform) in a folder, points the script
//! at it, and checks that it installs a binary that runs, and that it refuses a tarball
//! whose checksum does not match.

use std::path::PathBuf;
use std::process::Command;

const TARGETS: &[&str] = &["aarch64-apple-darwin", "x86_64-apple-darwin", "x86_64-unknown-linux-musl", "aarch64-unknown-linux-musl"];

fn sh(cmd: &str) {
    assert!(Command::new("sh").arg("-c").arg(cmd).status().unwrap().success(), "{cmd}");
}

#[test]
fn install_sh_installs_one_binary_and_checks_it() {
    let root = PathBuf::from(env!("CARGO_MANIFEST_DIR"));
    let work = std::env::temp_dir().join(format!("ava-install-{}", std::process::id()));
    let (release, bin) = (work.join("release"), work.join("bin"));
    let _ = std::fs::remove_dir_all(&work);
    std::fs::create_dir_all(&release).unwrap();
    std::fs::copy(env!("CARGO_BIN_EXE_ava"), release.join("ava")).unwrap();
    for t in TARGETS {
        sh(&format!("cd {0} && tar -czf ava-{t}.tar.gz ava && (shasum -a 256 ava-{t}.tar.gz 2>/dev/null || sha256sum ava-{t}.tar.gz) > ava-{t}.tar.gz.sha256", release.display()));
    }
    let run = || Command::new("sh").arg(root.join("install.sh")).env("AVA_URL", format!("file://{}", release.display())).env("AVA_BIN_DIR", &bin).output().unwrap();
    let out = run();
    let said = String::from_utf8_lossy(&out.stdout);
    assert!(out.status.success(), "{said}{}", String::from_utf8_lossy(&out.stderr));
    assert!(said.starts_with(&format!("installed ava {}", env!("CARGO_PKG_VERSION"))), "{said}");
    let v = Command::new(bin.join("ava")).arg("--version").output().unwrap();
    assert!(String::from_utf8_lossy(&v.stdout).starts_with("ava "));

    std::fs::remove_dir_all(&bin).unwrap();
    for t in TARGETS {
        std::fs::write(release.join(format!("ava-{t}.tar.gz.sha256")), "0000  x\n").unwrap();
    }
    let out = run();
    assert!(!out.status.success(), "a bad checksum must refuse");
    assert!(!bin.join("ava").exists(), "nothing installed");
    let _ = std::fs::remove_dir_all(&work);
}

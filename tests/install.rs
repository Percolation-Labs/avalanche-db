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
    let work = std::env::temp_dir().join(format!("midb-install-{}", std::process::id()));
    let (release, bin) = (work.join("release"), work.join("bin"));
    let _ = std::fs::remove_dir_all(&work);
    std::fs::create_dir_all(&release).unwrap();
    std::fs::copy(env!("CARGO_BIN_EXE_midb"), release.join("midb")).unwrap();
    for t in TARGETS {
        sh(&format!("cd {0} && tar -czf midb-{t}.tar.gz midb && (shasum -a 256 midb-{t}.tar.gz 2>/dev/null || sha256sum midb-{t}.tar.gz) > midb-{t}.tar.gz.sha256", release.display()));
    }
    let run = || Command::new("sh").arg(root.join("install.sh")).env("MIDB_URL", format!("file://{}", release.display())).env("MIDB_BIN_DIR", &bin).output().unwrap();
    let out = run();
    let said = String::from_utf8_lossy(&out.stdout);
    assert!(out.status.success(), "{said}{}", String::from_utf8_lossy(&out.stderr));
    assert!(said.starts_with(&format!("installed midb {}", env!("CARGO_PKG_VERSION"))), "{said}");
    let v = Command::new(bin.join("midb")).arg("--version").output().unwrap();
    assert!(String::from_utf8_lossy(&v.stdout).starts_with("midb "));

    std::fs::remove_dir_all(&bin).unwrap();
    for t in TARGETS {
        std::fs::write(release.join(format!("midb-{t}.tar.gz.sha256")), "0000  x\n").unwrap();
    }
    let out = run();
    assert!(!out.status.success(), "a bad checksum must refuse");
    assert!(!bin.join("midb").exists(), "nothing installed");
    let _ = std::fs::remove_dir_all(&work);
}

#[test]
fn install_sh_local_installs_from_a_clone_with_no_release() {
    let root = PathBuf::from(env!("CARGO_MANIFEST_DIR"));
    let bin = std::env::temp_dir().join(format!("midb-install-local-{}", std::process::id()));
    let _ = std::fs::remove_dir_all(&bin);
    // the build is this test's own binary: cargo is already holding the build directory
    let out = Command::new("sh").arg(root.join("install.sh")).arg("--local").env("CARGO", "true")
        .env("MIDB_LOCAL_BIN", env!("CARGO_BIN_EXE_midb")).env("MIDB_BIN_DIR", &bin).output().unwrap();
    let said = String::from_utf8_lossy(&out.stdout);
    assert!(out.status.success(), "{said}{}", String::from_utf8_lossy(&out.stderr));
    assert!(said.starts_with(&format!("installed midb {}", env!("CARGO_PKG_VERSION"))), "{said}");
    assert!(bin.join("midb").exists());
    let _ = std::fs::remove_dir_all(&bin);
}

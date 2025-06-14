# ensure_file.py

Warning: This is very alpha

Minimal idempotent file editor in Python.

Ensures lines or blocks are present or replaced in files, similar to `lineinfile`/`blockinfile` in Ansible, but with without the need to install a massive framework.

- Safe to run repeatedly (idempotent by design).
- Very easy to use in shell scripts

---

## Usage

```bash
./ensure_file.py FILE [OPTIONS]
```

---

## Options

| Option                      | Description                                                |
|-----------------------------|------------------------------------------------------------|
| `--line LINE`              | Ensure a specific line is present                          |
| `--block L1 L2 ...`        | Ensure a block is present (requires `--start` and `--end`) |
| `--start STR`              | Block start marker (required with `--block`)               |
| `--end STR`                | Block end marker (required with `--block`)                 |
| `--replace FROM TO`        | Replace a specific line (exact match)                      |
| `--replace-re PATTERN REPL`| Replace lines using regex pattern and replacement          |
| `-f`, `--force`            | Apply without prompting for confirmation                   |
| `-q`, `--quiet`            | Suppress output and diffs                                  |
| `-I`, `--idempotent-ok`    | Treat "already correct" as success (exit 0 instead of 4)   |

---

## Exit Codes

| Code | Meaning                        |
|------|--------------------------------|
| 0    | Success                        |
| 1    | Internal or argument error     |
| 2    | Permission denied              |
| 3    | No match found                 |
| 4    | No change needed (idempotent)  |
| 5    | File not found                 |

---

## Examples

### Ensure a line exists

```bash
./ensure_file.py /etc/sysctl.conf --line "vm.swappiness = 10"
```

### Ensure a line, force apply without prompt

```bash
./ensure_file.py /etc/sysctl.conf --line "fs.inotify.max_user_watches = 524288" -f
```

### Replace a line (exact match)

```bash
./ensure_file.py myapp.conf --replace "debug = true" "debug = false"
```

### Replace using regex

```bash
./ensure_file.py myapp.conf --replace-re "^loglevel\s*=.*" "loglevel = warning"
```

### Ensure a block (with start and end markers)

```bash
./ensure_file.py sshd_config \
  --block "PermitRootLogin no" "PasswordAuthentication no" \
  --start "# BEGIN hardening" --end "# END hardening"
```

### Run quietly, treat idempotent state as success

```bash
./ensure_file.py my.cnf --line "skip-networking" -q -I
```

---

## Tips

- Add newlines inside markers or block lines

# Secret scanning

The repository includes a SHA-pinned TruffleHog GitHub Actions workflow. Pull requests scan changed history; scheduled and manual runs scan the full checked-out Git history. Only **verified** secret detections fail the job, to reduce false positives.

Enable GitHub's native secret-scanning alerts and push protection in repository settings where available. Review unverified patterns separately, and scan released Docker images, archives and generated deployment artefacts. A green result is not proof that every historical secret or nonstandard credential was detected. Never paste detected secrets into public PRs or issue discussions; rotate and revoke them privately.

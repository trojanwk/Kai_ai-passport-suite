[简体中文](HANDOFF.zh_CN.md)

# AIHOT Implementation Handoff

Updated: 2026-11-01. Personal fork: `trojanwk/Kai_ai-passport-suite`; branch: `codex/aihot-news`; upstream baseline: `b754c7b1cadc8cb1c5abbba8de57e7ea4a1fe43d`.

The requested increment replaces Baidu trends with AIHOT Top 10 events, independent-source counts, bounded on-demand summaries, source attribution and event timestamps. Existing App ID 37, menu position, navigation and partition layout are preserved. Data is fetched directly through the device's Wi-Fi; one firmware installation is needed for the change, and subsequent news refreshes need no reflash.

The companion repair is retained in commit `45e1134`: pinned Bluetooth identity, reused notification subscriptions, bounded dictation setup retries, and separate authenticated-contact freshness. The installed Mac app already contains those fixes. Earlier real BLE navigation passed three reentry cycles; physical-button and actual dictation acceptance remains pending. Do not copy pairing credentials, signing keys, or private logs into Git.

Firmware identity: `passport_device`, version `0.5.21-aihot.1`, ESP-IDF v6.1, ESP32-C3, 8 MB, no PSRAM. ESP-IDF 5.5.3 remains installed separately. Run `./tools/validate.sh` for the complete gate. The delivered package's `manifest.json` is authoritative for its exact source commit, application hash, ELF hash, partition map and device-test status; see `releases/Kai_ai-passport-suite-0.5.21-aihot.1-*/` and the matching ignored debug bundle.

Validation evidence: synthetic host tests cover arbitrary chunks, escaped Unicode, bounds, invalid JSON/schema/ranks, source counts, trusted story URLs, summary fallback and timestamps under ASan/UBSan. A read-only live probe accepted ten real topics and one event summary. Added static Chinese text and representative live titles were checked against the generated font map. Neither a successful host test nor build proves device acceptance.

Build: PASS. Host tests: PASS (75 tests). Device tests: NOT RUN. The complete gate passed before handoff; final package provenance is recorded in its manifest.

Pending: user approval for flashing, USB device discovery, installed-partition compatibility, on-device startup, Chinese text/layout, TLS and RAM behavior, detail navigation, network failures, and voice/companion regression. No USB flash or full-chip erase has been performed or authorized. Offer application-only installation after confirming the existing layout; follow `docs/flash-guide.md` and record actual results here.

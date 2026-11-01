[简体中文](aihot.zh_CN.md)

# AIHOT on AI Passport

The existing `App::Hot` protocol ID is preserved. The menu now says **AI 热榜**, and the device calls the current anonymous [AIHOT v1 API](https://aihot.news/agent?tab=api), directly over Wi-Fi. The Mac companion is not required for the board.

## Behavior

- Up/Down selects a ranked event; Confirm opens or closes its detail. Long Confirm returns to the menu using the existing navigation rules.
- The list contains up to ten events in the order supplied by AIHOT. Its right-hand number is the count of independent sources, not Baidu heat, article count, or a synthetic score.
- A detail shows the title, a short event-summary excerpt, representative source, and the event's latest timestamp. Attribution remains visible as AIHOT.
- The board refreshes every ten minutes while open. Repeated refresh requests on that page reuse a board younger than one minute. Returning to a page starts a new page session.
- Event summaries are requested only when the corresponding detail is opened. They are reused for the lifetime of the page. When a valid `links.story` is absent, the device reports that no event summary is available.
- A failed board refresh retains the last complete board in the current page session. There is no persistent offline-news archive. Leaving the page releases its memory.
- Rate-limit and edge-security refusals are not automatically retried in a tight loop. No alternative user agent or browser impersonation is used.

## Data contract and limits

`GET /api/v1/hot-topics` supplies the rank, title, `sourceCount`, representative `source.name`, `latestAt`, and an optional story link. A validated same-host story link supplies the opaque identifier for `GET /api/v1/stories/{publicId}`. The story's `digest` is preferred; `latest` is the fallback. The reported story identity must match the requested identifier.

The parser is independent of ESP-IDF and LVGL, retains no JSON DOM or entire response, and bounds JSON depth, token storage, item count, and text lengths. It supports shuffled fields, arbitrary chunks, escaped quotes, and Unicode surrogate pairs. Invalid or incomplete responses do not replace a valid board. The ten event records occupy less than 6 KB, and the parser occupies less than 3 KB; host tests enforce both limits.

The application sends an anonymous random UUID stored under the `aihot_actor` NVS key. It does not send a hardware MAC address, companion pairing token, Wi-Fi credential, or account key. Responses are requested without compression because the existing ESP32 event sink does not implement decompression; only bounded selected fields are retained.

The board owns the network work in the existing worker task. Button callbacks continue to dispatch actions. Page teardown cancels the task and releases its event records. The partition table, application offset, existing NVS namespaces, and wake-word model offsets are unchanged.

## Verification

```bash
.venv/bin/python -m unittest tests/test_passport_aihot.py -v
```

Synthetic fixtures cover public API structure without redistributing actual news content. Checks include ASan/UBSan, field order, long values, Unicode, optional and hostile story URLs, empty boards, source counts, rank/count mismatches, truncated JSON, and UTC/offset timestamps. A live API probe verifies network reachability from the Mac; ESP32 TLS, screen rendering, physical buttons, and offline behavior remain separate device checks.

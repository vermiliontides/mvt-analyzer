# Cross-Domain Correlation Report

Backup date: `2026-05-28T11:23:38+00:00`  
Correlation window: ±15 min  
Timeline events indexed: 262611  
Alerts with a timestamp: 3  
Alerts without a timestamp (reported separately): 1

## Section 1 — Alert correlation (what mvt flagged, in context)

### `2026-05-10T21:37:17.486342+00:00` — MEDIUM — safari_history
> Redirect took less than a second! (0.27 milliseconds)
- **URL:** `http://gmail.com/`

**Correlated activity (±15 min, 22 event(s), excluding backup-internal churn):**

| Time | Module | Event |
| :--- | :--- | :--- |
| 21:23:28.389 | Datausage | mDNSResponder/com.linkedin.LinkedIn (Bundle ID: com.linkedin.LinkedIn, ID: 525) WWAN IN: 19675.0, WWAN OUT: 8232.0 |
| 21:23:49.151 | Datausage | mDNSResponder/com.google.Authenticator (Bundle ID: com.google.Authenticator, ID: 306) WWAN IN: 5148.0, WWAN OUT: 2204.0 |
| 21:25:40.538 | Datausage | Bitwarden/com.8bit.bitwarden (Bundle ID: com.8bit.bitwarden, ID: 285) WWAN IN: 1692334.0, WWAN OUT: 261044.0 |
| 21:25:41.351 | Datausage | mDNSResponder/com.8bit.bitwarden (Bundle ID: com.8bit.bitwarden, ID: 284) WWAN IN: 2090.0, WWAN OUT: 1227.0 |
| 21:34:10.439 | Datausage | mDNSResponder/com.8bit.bitwarden (Bundle ID: com.8bit.bitwarden, ID: 284) |
| 21:36:30.713 | Datausage | AccountsUISupportService/AccountsUISupportService (Bundle ID: AccountsUISupportService, ID: 188) |
| 21:37:17.486 ← ALERT | SafariHistory | Safari visit to http://gmail.com/ (ID: 2046, Visit ID: 18965) |
| 21:37:17.486 | SafariHistory | Safari visit to https://mail.google.com/mail/mu/?authuser=0 (ID: 927, Visit ID: 18966) |
| 21:37:18.744 | SafariHistory | Safari visit to https://mail.google.com/mail/mu/mp/683/?authuser=0 (ID: 2762, Visit ID: 18967) |
| 21:37:18.744 | SafariHistory | Safari visit to https://mail.google.com/mail/mu/mp/683/ (ID: 2289, Visit ID: 18968) |
| 21:37:19.563 | SafariHistory | Safari visit to https://mail.google.com/mail/mu/mp/683/#tl/Inbox (ID: 1432, Visit ID: 18969) |
| 21:37:22.846 | SafariHistory | Safari visit to https://gmail.app.goo.gl/?link=https://mail.google.com&pt=9008&mt=8&isi=422689480&ibi=com.google.Gmail&ct=sp-stn-p-3 (ID: 6… |
| 21:37:22.846 | SafariHistory | Safari visit to https://preview.app.goo.gl/gmail.app.goo.gl?link=https://mail.google.com&isi=422689480&ibi=com.google.Gmail&ct=sp-stn-p-3&m… |
| 21:38:30.080 | OSAnalyticsADDaily | com.google.Gmail WIFI IN: 303743345.0, WIFI OUT: 51943408.0 - WWAN IN: 152062263.0, WWAN OUT: 34711420.0 |
| 21:38:30.595 | Datausage | storekitd/com.google.Gmail (Bundle ID: com.google.Gmail, ID: 878) |
| 21:38:36.569 | Datausage | mDNSResponder/com.google.Gmail (Bundle ID: com.google.Gmail, ID: 879) WWAN IN: 8488.0, WWAN OUT: 8094.0 |
| 21:38:36.570 | Datausage | mDNSResponder/com.google.Gmail (Bundle ID: com.google.Gmail, ID: 879) |
| 21:39:25.743 | Datausage | Gmail/com.google.Gmail (Bundle ID: com.google.Gmail, ID: 880) |
| 21:40:08.216 | Datausage | passwordbreachd/com.apple.datausage.security (Bundle ID: com.apple.datausage.security, ID: 59) WWAN IN: 93099828.0, WWAN OUT: 3305327.0 |
| 21:40:21.001 | Datausage | passwordbreachd/com.apple.datausage.security (Bundle ID: com.apple.datausage.security, ID: 59) |
| 21:40:26.000 | InteractionC | [com.apple.mobilemail] 8C493A40-947E-4B13-AFB5-28B7978937A2 - from Indeed (donotreply@match.indeed.com) to  (): |
| 21:40:38.172 | Datausage | com.apple.WebKit.Networking/com.google.Gmail (Bundle ID: com.google.Gmail, ID: 881) |

_(+89 low-signal backup-bookkeeping event(s) omitted: 89 Manifest)_

### `2026-05-24T03:31:07.006663+00:00` — MEDIUM — safari_history
> Redirect took less than a second! (0.396 milliseconds)
- **URL:** `http://gmail.com/`

**Correlated activity (±15 min, 210 event(s), excluding backup-internal churn):**

| Time | Module | Event |
| :--- | :--- | :--- |
| 03:16:07.793 | SafariHistory | Safari visit to https://account.google.com/advanced-protection/enroll/details (ID: 6893, Visit ID: 21097) |
| 03:16:07.793 | SafariHistory | Safari visit to https://accounts.google.com/v3/signin/accountchooser?continue=https%3A%2F%2Fmyaccount.google.com%2Fadvanced-protection%2Fen… |
| 03:16:07.996 | SafariHistory | Safari visit to https://accounts.google.com/v3/signin/accountchooser?continue=https%3A%2F%2Fmyaccount.google.com%2Fadvanced-protection%2Fen… |
| 03:16:10.633 | SafariHistory | Safari visit to https://accounts.google.com/v3/signin/challenge/pk?TL=APouJz4q6OYKc4qc8140D8kR4D_dyN_Q8EJUtKznypW6hmBgfebWKwjjEpE3k4W9&cid=… |
| 03:16:26.316 | SafariHistory | Safari visit to https://accounts.google.com/v3/signin/speedbump/passkeyenrollment?TL=APouJz4q6OYKc4qc8140D8kR4D_dyN_Q8EJUtKznypW6hmBgfebWKw… |
| 03:16:26.652 | SafariHistory | Safari visit to https://accounts.google.com/v3/signin/speedbump/passkeyenrollment?TL=APouJz4q6OYKc4qc8140D8kR4D_dyN_Q8EJUtKznypW6hmBgfebWKw… |
| 03:16:32.714 | SafariHistory | Safari visit to https://accounts.youtube.com/accounts/SetSID?ssdc=1&sidt=ALWU2ctFXH9CYuCv3vtiaF0beNRsl5YyRQl6KjBGFJ/Uamrwbx/ORDItsTahJZqXuk… |
| 03:16:32.714 | SafariHistory | Safari visit to https://accounts.google.com/v3/signin/challenge/ipp/consent?TL=APouJz5xLAB3GVof5pNd4cdAAtcmxjOl9FZsc_Gwe2iHgc46Q22L6TsdjyhH… |
| 03:16:33.096 | SafariHistory | Safari visit to https://accounts.google.com/v3/signin/challenge/ipp/consent?TL=APouJz5xLAB3GVof5pNd4cdAAtcmxjOl9FZsc_Gwe2iHgc46Q22L6TsdjyhH… |
| 03:16:36.893 | SafariHistory | Safari visit to https://accounts.google.com/v3/signin/challenge/selection?TL=APouJz5xLAB3GVof5pNd4cdAAtcmxjOl9FZsc_Gwe2iHgc46Q22L6TsdjyhHmS… |
| 03:16:39.500 | SafariHistory | Safari visit to https://accounts.google.com/v3/signin/challenge/ipp/verify?TL=APouJz5xLAB3GVof5pNd4cdAAtcmxjOl9FZsc_Gwe2iHgc46Q22L6TsdjyhHm… |
| 03:16:43.911 | SafariHistory | Safari visit to https://accounts.google.com/v3/signin/challenge/selection?TL=APouJz5xLAB3GVof5pNd4cdAAtcmxjOl9FZsc_Gwe2iHgc46Q22L6TsdjyhHmS… |
| 03:16:47.760 | SafariHistory | Safari visit to https://accounts.google.com/AccountChooser?authuser=2&continue=https%3A%2F%2Fmyaccount.google.com%2Fu%2F2%2Fadvanced-protec… |
| 03:16:47.761 | SafariHistory | Safari visit to https://accounts.google.com/v3/signin/accountchooser?authuser=2&continue=https%3A%2F%2Fmyaccount.google.com%2Fu%2F2%2Fadvan… |
| 03:16:47.861 | SafariHistory | Safari visit to https://accounts.google.com/v3/signin/accountchooser?authuser=2&continue=https%3A%2F%2Fmyaccount.google.com%2Fu%2F2%2Fadvan… |
| 03:16:50.900 | SafariHistory | Safari visit to https://accounts.google.com/v3/signin/challenge/pk?TL=APouJz58nr6Qv-XBkbJjn6GtVHrC_ijOQ1FNnu4tVpNnTh7ZTjolQ9GIFSyAno1l&auth… |
| 03:16:55.733 | SafariHistory | Safari visit to https://accounts.google.com/v3/signin/challenge/pk/presend?TL=APouJz58nr6Qv-XBkbJjn6GtVHrC_ijOQ1FNnu4tVpNnTh7ZTjolQ9GIFSyAn… |
| 03:16:57.425 | SafariHistory | Safari visit to https://accounts.google.com/v3/signin/challenge/selection?TL=APouJz58nr6Qv-XBkbJjn6GtVHrC_ijOQ1FNnu4tVpNnTh7ZTjolQ9GIFSyAno… |
| 03:16:59.772 | SafariHistory | Safari visit to https://accounts.google.com/v3/signin/challenge/pk/presend?TL=APouJz58nr6Qv-XBkbJjn6GtVHrC_ijOQ1FNnu4tVpNnTh7ZTjolQ9GIFSyAn… |
| 03:17:01.042 | SafariHistory | Safari visit to https://accounts.google.com/v3/signin/challenge/selection?TL=APouJz58nr6Qv-XBkbJjn6GtVHrC_ijOQ1FNnu4tVpNnTh7ZTjolQ9GIFSyAno… |
| 03:17:02.436 | SafariHistory | Safari visit to https://accounts.google.com/v3/signin/challenge/pwd?TL=APouJz58nr6Qv-XBkbJjn6GtVHrC_ijOQ1FNnu4tVpNnTh7ZTjolQ9GIFSyAno1l&aut… |
| 03:17:10.425 | SafariHistory | Safari visit to https://accounts.google.com/v3/signin/challenge/dp?TL=APouJz58nr6Qv-XBkbJjn6GtVHrC_ijOQ1FNnu4tVpNnTh7ZTjolQ9GIFSyAno1l&auth… |
| 03:17:20.000 | WebkitResourceLoadStatistics | Webkit resource loaded from google.com by app in domain AppDomain-com.google.Gmail |
| 03:17:23.179 | SafariHistory | Safari visit to https://account.google.com/advanced-protection/enroll/details (ID: 6893, Visit ID: 21119) |
| 03:17:23.179 | SafariHistory | Safari visit to https://accounts.google.com/v3/signin/accountchooser?continue=https%3A%2F%2Fmyaccount.google.com%2Fadvanced-protection%2Fen… |
| 03:17:23.302 | SafariHistory | Safari visit to https://accounts.google.com/v3/signin/accountchooser?continue=https%3A%2F%2Fmyaccount.google.com%2Fadvanced-protection%2Fen… |
| 03:17:24.447 | SafariHistory | Safari visit to https://accounts.google.com/ServiceLogin?authuser=1&continue=https%3A%2F%2Fmyaccount.google.com%2Fadvanced-protection%2Fenr… |
| 03:17:24.453 | SafariHistory | Safari visit to https://accounts.google.com/ServiceLogin (ID: 62, Visit ID: 21123) |
| 03:17:25.631 | SafariHistory | Safari visit to https://myaccount.google.com/accounts/SetOSID (ID: 6918, Visit ID: 21124) |
| 03:17:25.631 | SafariHistory | Safari visit to https://accounts.google.com/v3/signin/challenge/pk?TL=APouJz6jXaLH27xCHsQpv3nsADZSixTWbZ3thwCya9CGqVwxXzS96aHnvw5pZrEv&auth… |
| 03:17:25.780 | SafariHistory | Safari visit to https://accounts.google.com/v3/signin/challenge/pk?TL=APouJz6jXaLH27xCHsQpv3nsADZSixTWbZ3thwCya9CGqVwxXzS96aHnvw5pZrEv&auth… |
| 03:17:27.175 | SafariHistory | Safari visit to https://accounts.google.com/v3/signin/challenge/pk/presend?TL=APouJz6jXaLH27xCHsQpv3nsADZSixTWbZ3thwCya9CGqVwxXzS96aHnvw5pZ… |
| 03:17:28.910 | SafariHistory | Safari visit to https://accounts.google.com/ServiceLogin?authuser=2&continue=https%3A%2F%2Fmyaccount.google.com%2Fadvanced-protection%2Fenr… |
| 03:17:28.913 | SafariHistory | Safari visit to https://accounts.google.com/ServiceLogin (ID: 62, Visit ID: 21129) |
| 03:17:30.229 | SafariHistory | Safari visit to https://myaccount.google.com/accounts/SetOSID (ID: 6918, Visit ID: 21130) |
| 03:17:30.229 | SafariHistory | Safari visit to https://accounts.google.com/v3/signin/challenge/ipp/consent?TL=APouJz4biTb6IhlibWkOs9mVfq-Gu_3CY7e9M5LKDXHF60cXkUYB4BxMdyCw… |
| 03:17:30.347 | SafariHistory | Safari visit to https://accounts.google.com/v3/signin/challenge/ipp/consent?TL=APouJz4biTb6IhlibWkOs9mVfq-Gu_3CY7e9M5LKDXHF60cXkUYB4BxMdyCw… |
| 03:17:33.397 | SafariHistory | Safari visit to https://accounts.google.com/v3/signin/challenge/selection?TL=APouJz4biTb6IhlibWkOs9mVfq-Gu_3CY7e9M5LKDXHF60cXkUYB4BxMdyCw_I… |
| 03:17:35.526 | SafariHistory | Safari visit to https://accounts.google.com/v3/signin/challenge/ipp/verify?TL=APouJz4biTb6IhlibWkOs9mVfq-Gu_3CY7e9M5LKDXHF60cXkUYB4BxMdyCw_… |
| 03:17:37.946 | SafariHistory | Safari visit to https://accounts.google.com/v3/signin/challenge/selection?TL=APouJz4biTb6IhlibWkOs9mVfq-Gu_3CY7e9M5LKDXHF60cXkUYB4BxMdyCw_I… |
| 03:17:39.711 | SafariHistory | Safari visit to https://accounts.google.com/v3/signin/challenge/ipp/verify?TL=APouJz4biTb6IhlibWkOs9mVfq-Gu_3CY7e9M5LKDXHF60cXkUYB4BxMdyCw_… |
| 03:17:43.186 | SafariHistory | Safari visit to https://accounts.google.com/AccountChooser?authuser=2&continue=https%3A%2F%2Fmyaccount.google.com%2Fu%2F2%2Fadvanced-protec… |
| 03:17:43.186 | SafariHistory | Safari visit to https://accounts.google.com/v3/signin/accountchooser?authuser=2&continue=https%3A%2F%2Fmyaccount.google.com%2Fu%2F2%2Fadvan… |
| 03:17:43.264 | SafariHistory | Safari visit to https://accounts.google.com/v3/signin/accountchooser?authuser=2&continue=https%3A%2F%2Fmyaccount.google.com%2Fu%2F2%2Fadvan… |
| 03:17:46.600 | SafariHistory | Safari visit to https://accounts.google.com/v3/signin/challenge/pk?TL=APouJz6HFgOqFm5MybX3j4j2kpOY2Pt-ZWkQ6mXY1aKVynj-aYZ42TH8BunNMGBH&auth… |
| 03:17:48.158 | SafariHistory | Safari visit to https://accounts.google.com/v3/signin/challenge/pk/presend?TL=APouJz6HFgOqFm5MybX3j4j2kpOY2Pt-ZWkQ6mXY1aKVynj-aYZ42TH8BunNM… |
| 03:17:49.388 | SafariHistory | Safari visit to https://accounts.google.com/v3/signin/challenge/selection?TL=APouJz6HFgOqFm5MybX3j4j2kpOY2Pt-ZWkQ6mXY1aKVynj-aYZ42TH8BunNMG… |
| 03:17:51.158 | SafariHistory | Safari visit to https://accounts.google.com/v3/signin/challenge/pwd?TL=APouJz6HFgOqFm5MybX3j4j2kpOY2Pt-ZWkQ6mXY1aKVynj-aYZ42TH8BunNMGBH&aut… |
| 03:18:00.954 | SafariHistory | Safari visit to https://accounts.google.com/v3/signin/challenge/ipp/consent?TL=APouJz6HFgOqFm5MybX3j4j2kpOY2Pt-ZWkQ6mXY1aKVynj-aYZ42TH8BunN… |
| 03:18:03.294 | SafariHistory | Safari visit to https://accounts.google.com/v3/signin/challenge/selection?TL=APouJz6HFgOqFm5MybX3j4j2kpOY2Pt-ZWkQ6mXY1aKVynj-aYZ42TH8BunNMG… |
| 03:18:11.608 | SafariHistory | Safari visit to https://accounts.google.com/AccountChooser?authuser=2&continue=https%3A%2F%2Fmyaccount.google.com%2Fu%2F2%2Fadvanced-protec… |
| 03:18:11.609 | SafariHistory | Safari visit to https://accounts.google.com/v3/signin/accountchooser?authuser=2&continue=https%3A%2F%2Fmyaccount.google.com%2Fu%2F2%2Fadvan… |
| 03:18:11.679 | SafariHistory | Safari visit to https://accounts.google.com/v3/signin/accountchooser?authuser=2&continue=https%3A%2F%2Fmyaccount.google.com%2Fu%2F2%2Fadvan… |
| 03:20:03.627 | InteractionC | [com.google.Gmail] None - from Google (no-reply@accounts.google.com) to  (): |
| 03:20:04.001 | InteractionC | [com.google.Gmail] None - from Google (no-reply@accounts.google.com) to  (): |
| 03:20:30.052 | InteractionC | [org.whispersystems.signal] None - from Rob (+18303596439) to  (): |
| 03:20:30.211 | InteractionC | [org.whispersystems.signal] None - from Rob (+18303596439) to  (): |
| 03:20:34.501 | InteractionC | [org.whispersystems.signal] None - from Rob (+18303596439) to  (): |
| 03:20:34.514 | InteractionC | [org.whispersystems.signal] None - from Rob (+18303596439) to  (): |
| 03:21:00.342 | InteractionC | [org.whispersystems.signal] None - from Rob (+18303596439) to  (): |
| 03:21:00.372 | InteractionC | [org.whispersystems.signal] None - from Rob (+18303596439) to  (): |
| 03:21:09.797 | InteractionC | [org.whispersystems.signal] None - from Rob (+18303596439) to  (): |
| 03:21:09.811 | InteractionC | [org.whispersystems.signal] None - from Rob (+18303596439) to  (): |
| 03:21:18.703 | InteractionC | [org.whispersystems.signal] None - from Rob (+18303596439) to  (): |
| 03:21:18.719 | InteractionC | [org.whispersystems.signal] None - from Rob (+18303596439) to  (): |
| 03:21:53.302 | InteractionC | [org.whispersystems.signal] None - from Rob (+18303596439) to  (): |
| 03:21:53.313 | InteractionC | [org.whispersystems.signal] None - from Rob (+18303596439) to  (): |
| 03:22:05.217 | InteractionC | [org.whispersystems.signal] None - from Rob (+18303596439) to  (): |
| 03:22:05.232 | InteractionC | [org.whispersystems.signal] None - from Rob (+18303596439) to  (): |
| 03:22:44.321 | InteractionC | [org.whispersystems.signal] None - from Rob (+18303596439) to  (): |
| 03:22:44.337 | InteractionC | [org.whispersystems.signal] None - from Rob (+18303596439) to  (): |
| 03:24:13.479 | InteractionC | [com.google.Gmail] None - from Google (no-reply@accounts.google.com) to  (): |
| 03:24:13.516 | InteractionC | [com.google.Gmail] None - from Google (no-reply@accounts.google.com) to  (): |
| 03:24:29.639 | SafariHistory | Safari visit to https://www.google.com/url?q=https://accounts.google.com/AccountChooser?Email%3Dsolsticeskies19@gmail.com%26continue%3Dhttp… |
| 03:24:29.639 | SafariHistory | Safari visit to https://accounts.google.com/v3/signin/confirmidentifier?authuser=2&continue=https%3A%2F%2Fmyaccount.google.com%2Falert%2Fnt… |
| 03:24:30.012 | SafariHistory | Safari visit to https://accounts.google.com/v3/signin/confirmidentifier?authuser=2&continue=https%3A%2F%2Fmyaccount.google.com%2Falert%2Fnt… |
| 03:24:31.551 | SafariHistory | Safari visit to https://accounts.google.com/v3/signin/challenge/pk?TL=APouJz7Zr36m7kMLRg0iiBHKNQJcsA3vUv2UFTQpOP8jNBGkXWq1BeGYpcp_HJV5&auth… |
| 03:24:55.101 | SafariHistory | Safari visit to https://accounts.youtube.com/accounts/SetSID?ssdc=1&sidt=ALWU2cv914F6utXyF0JvIBOz4d8pLQH4xLn8lb7Xiad/oBE/M1f%2B6JpnbLfp4MTk… |
| 03:24:55.101 | SafariHistory | Safari visit to https://myaccount.google.com/u/2/notifications/eid/5461218226973519122?rfn=5&rfnc=1&et=0 (ID: 6963, Visit ID: 21154) |
| 03:24:55.402 | SafariHistory | Safari visit to https://myaccount.google.com/u/2/notifications/eid/5461218226973519122?rfn=5&rfnc=1&et=0 (ID: 6963, Visit ID: 21155) |
| 03:24:58.603 | SafariHistory | Safari visit to https://myaccount.google.com/u/2/notifications/eid/5461218226973519122?rfn=5&rfnc=1&et=0 (ID: 6963, Visit ID: 21156) |
| 03:25:00.667 | SafariHistory | Safari visit to https://myaccount.google.com/u/2/notifications/eid/5461218226973519122?rfn=5&rfnc=1&et=0 (ID: 6963, Visit ID: 21157) |
| 03:25:00.673 | SafariHistory | Safari visit to https://myaccount.google.com/u/2/notifications?rfn%3D5%26rfnc%3D1%26et%3D0&rfnc=1&origin=1 (ID: 6965, Visit ID: 21158) |
| 03:25:07.443 | SafariHistory | Safari visit to https://myaccount.google.com/u/2/notifications/eid/5083444787151457922?rfnc=1&origin=1&continue=https%3A%2F%2Fmyaccount.goo… |
| 03:25:10.181 | SafariHistory | Safari visit to https://myaccount.google.com/u/2/notifications?rfn%3D5%26rfnc%3D1%26et%3D0&rfnc=1&origin=1 (ID: 6965, Visit ID: 21160) |
| 03:25:11.211 | SafariHistory | Safari visit to https://myaccount.google.com/u/2/notifications/eid/415666068150973257?rfnc=1&origin=1&continue=https%3A%2F%2Fmyaccount.goog… |
| 03:25:13.805 | SafariHistory | Safari visit to https://myaccount.google.com/u/2/notifications/eid/415666068150973257?rfnc=1&origin=1&continue=https%3A%2F%2Fmyaccount.goog… |
| 03:25:15.027 | SafariHistory | Safari visit to https://myaccount.google.com/u/2/notifications/eid/415666068150973257?rfnc=1&origin=1&continue=https%3A%2F%2Fmyaccount.goog… |
| 03:25:16.814 | SafariHistory | Safari visit to https://myaccount.google.com/u/2/notifications?rfn%3D5%26rfnc%3D1%26et%3D0&rfnc=1&origin=1 (ID: 6965, Visit ID: 21164) |
| 03:25:17.748 | SafariHistory | Safari visit to https://myaccount.google.com/u/2/notifications/eid/-4127431715414014665?rfnc=1&origin=1&continue=https%3A%2F%2Fmyaccount.go… |
| 03:25:22.724 | SafariHistory | Safari visit to https://myaccount.google.com/u/2/notifications/eid/-4127431715414014665?rfnc=1&origin=1&continue=https%3A%2F%2Fmyaccount.go… |
| 03:25:23.612 | SafariHistory | Safari visit to https://myaccount.google.com/u/2/notifications/eid/-4127431715414014665?rfnc=1&origin=1&continue=https%3A%2F%2Fmyaccount.go… |
| 03:25:24.935 | SafariHistory | Safari visit to https://myaccount.google.com/u/2/notifications?rfn%3D5%26rfnc%3D1%26et%3D0&rfnc=1&origin=1 (ID: 6965, Visit ID: 21168) |
| 03:25:26.687 | SafariHistory | Safari visit to https://myaccount.google.com/u/2/notifications/eid/-4127431715414014665?rfnc=1&origin=1&continue=https%3A%2F%2Fmyaccount.go… |
| 03:25:26.949 | SafariHistory | Safari visit to https://myaccount.google.com/u/2/notifications/eid/-4127431715414014665?rfnc=1&origin=1&continue=https%3A%2F%2Fmyaccount.go… |
| 03:25:28.459 | SafariHistory | Safari visit to https://myaccount.google.com/u/2/notifications/eid/-4127431715414014665?rfnc=1&origin=1&continue=https%3A%2F%2Fmyaccount.go… |
| 03:25:28.531 | SafariHistory | Safari visit to https://myaccount.google.com/u/2/notifications/eid/-4127431715414014665?rfnc=1&origin=1&continue=https%3A%2F%2Fmyaccount.go… |
| 03:25:29.283 | SafariHistory | Safari visit to https://myaccount.google.com/u/2/notifications/eid/-4127431715414014665?rfnc=1&origin=1&continue=https%3A%2F%2Fmyaccount.go… |
| 03:25:30.620 | SafariHistory | Safari visit to https://myaccount.google.com/u/2/notifications?rfn%3D5%26rfnc%3D1%26et%3D0&rfnc=1&origin=1 (ID: 6965, Visit ID: 21174) |
| 03:25:32.658 | SafariHistory | Safari visit to https://myaccount.google.com/u/2/notifications/eid/-4593015348725195515?rfnc=1&origin=1&continue=https%3A%2F%2Fmyaccount.go… |
| 03:25:34.555 | SafariHistory | Safari visit to https://myaccount.google.com/u/2/notifications?rfn%3D5%26rfnc%3D1%26et%3D0&rfnc=1&origin=1 (ID: 6965, Visit ID: 21176) |
| 03:25:35.305 | SafariHistory | Safari visit to https://myaccount.google.com/u/2/notifications/eid/-1395023262223213057?rfnc=1&origin=1&continue=https%3A%2F%2Fmyaccount.go… |
| 03:25:36.558 | SafariHistory | Safari visit to https://myaccount.google.com/u/2/notifications/eid/-1395023262223213057?rfnc=1&origin=1&continue=https%3A%2F%2Fmyaccount.go… |
| 03:25:37.454 | SafariHistory | Safari visit to https://myaccount.google.com/u/2/notifications/eid/-1395023262223213057?rfnc=1&origin=1&continue=https%3A%2F%2Fmyaccount.go… |
| 03:25:38.560 | SafariHistory | Safari visit to https://myaccount.google.com/u/2/notifications?rfn%3D5%26rfnc%3D1%26et%3D0&rfnc=1&origin=1 (ID: 6965, Visit ID: 21180) |
| 03:25:40.927 | SafariHistory | Safari visit to https://myaccount.google.com/u/2/notifications/eid/6370433537078186289?rfnc=1&origin=1&continue=https%3A%2F%2Fmyaccount.goo… |
| 03:25:42.845 | SafariHistory | Safari visit to https://myaccount.google.com/u/2/notifications?rfn%3D5%26rfnc%3D1%26et%3D0&rfnc=1&origin=1 (ID: 6965, Visit ID: 21182) |
| 03:25:47.604 | SafariHistory | Safari visit to https://myaccount.google.com/u/2/notifications/eid/-7316669606693886805?rfnc=1&origin=1&continue=https%3A%2F%2Fmyaccount.go… |
| 03:25:48.503 | SafariHistory | Safari visit to https://myaccount.google.com/u/2/notifications/eid/-7316669606693886805?rfnc=1&origin=1&continue=https%3A%2F%2Fmyaccount.go… |
| 03:25:50.850 | SafariHistory | Safari visit to https://myaccount.google.com/u/2/notifications/eid/-7316669606693886805?rfnc=1&origin=1&continue=https%3A%2F%2Fmyaccount.go… |
| 03:25:51.908 | SafariHistory | Safari visit to https://myaccount.google.com/u/2/notifications/eid/-7316669606693886805?rfnc=1&origin=1&continue=https%3A%2F%2Fmyaccount.go… |
| 03:25:52.926 | SafariHistory | Safari visit to https://myaccount.google.com/u/2/security-checkup?rfn%3D5%26rfnc%3D1%26et%3D0&rfnc=1&origin=1&continue=https%3A%2F%2Fmyacco… |
| 03:25:53.202 | SafariHistory | Safari visit to https://myaccount.google.com/u/2/security-checkup?rfn%3D5%26rfnc%3D1%26et%3D0&rfnc=1&origin=1&continue=https%3A%2F%2Fmyacco… |
| 03:25:55.198 | SafariHistory | Safari visit to https://myaccount.google.com/u/2/security-checkup/1?rfn%3D5%26rfnc%3D1%26et%3D0&rfnc=1&origin=1&continue=https%3A%2F%2Fmyac… |
| 03:26:01.905 | SafariHistory | Safari visit to https://myaccount.google.com/security?authuser=2&authuser=2 (ID: 6976, Visit ID: 21190) |
| 03:26:01.905 | SafariHistory | Safari visit to https://myaccount.google.com/u/2/security (ID: 6975, Visit ID: 21191) |
| 03:26:02.160 | SafariHistory | Safari visit to https://myaccount.google.com/u/2/security (ID: 6975, Visit ID: 21192) |
| 03:26:12.461 | SafariHistory | Safari visit to https://myaccount.google.com/u/2/signinoptions/twosv (ID: 6977, Visit ID: 21193) |
| 03:26:12.461 | SafariHistory | Safari visit to https://accounts.google.com/v3/signin/challenge/dp?TL=APouJz7_II58SCKX17OT2kRBOwjW9ujMhe_2T896l9x3VSsweM391VK3__obrR9s&auth… |
| 03:26:12.680 | SafariHistory | Safari visit to https://accounts.google.com/v3/signin/challenge/dp?TL=APouJz7_II58SCKX17OT2kRBOwjW9ujMhe_2T896l9x3VSsweM391VK3__obrR9s&auth… |
| 03:26:24.765 | SafariHistory | Safari visit to https://accounts.google.com/v3/signin/rejected?TL=APouJz7_II58SCKX17OT2kRBOwjW9ujMhe_2T896l9x3VSsweM391VK3__obrR9s&authuser… |
| 03:27:39.642 | InteractionC | [org.whispersystems.signal] None - from Rob (+18303596439) to  (): |
| 03:27:39.772 | InteractionC | [org.whispersystems.signal] None - from Rob (+18303596439) to  (): |
| 03:29:04.478 | InteractionC | [org.whispersystems.signal] None - from Rob (+18303596439) to  (): |
| 03:29:04.494 | InteractionC | [org.whispersystems.signal] None - from Rob (+18303596439) to  (): |
| 03:29:16.258 | InteractionC | [org.whispersystems.signal] None - from Rob (+18303596439) to  (): |
| 03:29:16.275 | InteractionC | [org.whispersystems.signal] None - from Rob (+18303596439) to  (): |
| 03:29:33.974 | SafariHistory | Safari visit to https://accounts.google.com/v3/signin/rejected?TL=APouJz7_II58SCKX17OT2kRBOwjW9ujMhe_2T896l9x3VSsweM391VK3__obrR9s&authuser… |
| 03:29:34.404 | SafariHistory | Safari visit to https://accounts.google.com/v3/signin/rejected?TL=APouJz7_II58SCKX17OT2kRBOwjW9ujMhe_2T896l9x3VSsweM391VK3__obrR9s&authuser… |
| 03:29:37.506 | SafariHistory | Safari visit to https://accounts.google.com/restart?authuser=2&continue=https://myaccount.google.com/u/2/signinoptions/twosv&dsh=S-65303568… |
| 03:29:37.506 | SafariHistory | Safari visit to https://accounts.google.com/v3/signin/challenge/dp?TL=APouJz5efa4Dhoi2WkJSjkYMF3M7lKj-LxSuLigReh31LhP0IOTVUXWLEPUGw3bY&auth… |
| 03:29:37.703 | SafariHistory | Safari visit to https://accounts.google.com/v3/signin/challenge/dp?TL=APouJz5efa4Dhoi2WkJSjkYMF3M7lKj-LxSuLigReh31LhP0IOTVUXWLEPUGw3bY&auth… |
| 03:29:50.000 | WebkitResourceLoadStatistics | Webkit resource loaded from signaler-pa.googleapis.com by app in domain AppDomain-com.apple.mobilesafari |
| 03:29:54.412 | SafariHistory | Safari visit to https://accounts.youtube.com/accounts/SetSID?ssdc=1&sidt=ALWU2csFb6fAsOTaESL53CapkLbh2F5fOJGu7IPQlPdGsmSb7J32%2Bpkp9NaHomP2… |
| 03:29:54.412 | SafariHistory | Safari visit to https://myaccount.google.com/u/2/signinoptions/twosv?rapt=AEjHL4O-kbb_tod2gNegWcAkDs4bWtvHktlb8ixzcr6OSW4UGKwyeKi9bLVJiVr-d… |
| 03:29:54.778 | SafariHistory | Safari visit to https://myaccount.google.com/u/2/signinoptions/twosv?rapt=AEjHL4O-kbb_tod2gNegWcAkDs4bWtvHktlb8ixzcr6OSW4UGKwyeKi9bLVJiVr-d… |
| 03:30:01.234 | SafariHistory | Safari visit to https://myaccount.google.com/signinoptions/passkeys?continue=https%3A%2F%2Fmyaccount.google.com%2Fsigninoptions%2Ftwosv%3Fa… |
| 03:30:01.234 | SafariHistory | Safari visit to https://accounts.google.com/v3/signin/challenge/ipp/consent?TL=APouJz4QTM8sL0HCGNlc7x72GtlFSAT5DA8UFTAYp-IdNTBY79Z4HEj8lu8F… |
| 03:30:01.391 | SafariHistory | Safari visit to https://accounts.google.com/v3/signin/challenge/ipp/consent?TL=APouJz4QTM8sL0HCGNlc7x72GtlFSAT5DA8UFTAYp-IdNTBY79Z4HEj8lu8F… |
| 03:30:14.347 | SafariHistory | Safari visit to https://myaccount.google.com/u/2/signinoptions/twosv?rapt=AEjHL4O-kbb_tod2gNegWcAkDs4bWtvHktlb8ixzcr6OSW4UGKwyeKi9bLVJiVr-d… |
| 03:30:15.547 | SafariHistory | Safari visit to https://myaccount.google.com/u/2/signinoptions/twosv?rapt=AEjHL4O-kbb_tod2gNegWcAkDs4bWtvHktlb8ixzcr6OSW4UGKwyeKi9bLVJiVr-d… |
| 03:30:18.246 | InteractionC | [com.google.Gmail] None - from Google (no-reply@accounts.google.com) to  (): |
| 03:30:18.294 | InteractionC | [com.google.Gmail] None - from Google (no-reply@accounts.google.com) to  (): |
| 03:30:27.352 | SafariHistory | Safari visit to https://myaccount.google.com/u/2/security?rapt=AEjHL4O-kbb_tod2gNegWcAkDs4bWtvHktlb8ixzcr6OSW4UGKwyeKi9bLVJiVr-d1UIqtypPCox… |
| 03:30:27.541 | SafariHistory | Safari visit to https://myaccount.google.com/u/2/security?rapt=AEjHL4O-kbb_tod2gNegWcAkDs4bWtvHktlb8ixzcr6OSW4UGKwyeKi9bLVJiVr-d1UIqtypPCox… |
| 03:30:36.947 | SafariHistory | Safari visit to https://myaccount.google.com/u/2/device-activity?continue=https%3A%2F%2Fmyaccount.google.com%2Fu%2F2%2Fsecurity%3Frapt%3DAE… |
| 03:30:40.029 | SafariHistory | Safari visit to https://myaccount.google.com/u/2/device-activity/id/IMOS9Zm5ld7WZA?continue=https%3A%2F%2Fmyaccount.google.com%2Fu%2F2%2Fde… |
| 03:30:40.029 | SafariHistory | Safari visit to https://accounts.google.com/v3/signin/challenge/ipp/consent?TL=APouJz71FLFEl0xJZe7T1Dl6-_CkMg2AMhBBA8yvwDQBzqj8bU1bDTRoAHNG… |
| 03:30:40.140 | SafariHistory | Safari visit to https://accounts.google.com/v3/signin/challenge/ipp/consent?TL=APouJz71FLFEl0xJZe7T1Dl6-_CkMg2AMhBBA8yvwDQBzqj8bU1bDTRoAHNG… |
| 03:30:47.804 | SafariHistory | Safari visit to https://accounts.google.com/v3/signin/accountchooser?authuser=2&continue=https%3A%2F%2Fmyaccount.google.com%2Fu%2F2%2Fadvan… |
| 03:30:47.940 | SafariHistory | Safari visit to https://accounts.google.com/v3/signin/accountchooser?authuser=2&continue=https%3A%2F%2Fmyaccount.google.com%2Fu%2F2%2Fadvan… |
| 03:30:50.890 | SafariHistory | Safari visit to https://accounts.google.com/v3/signin/challenge/pk?TL=APouJz5fd79Z_QU0-onAlnrDT3HYORCRvc6xbQbe-S4rW3qnTj8pVC_TF2mWK7tD&auth… |
| 03:30:52.627 | SafariHistory | Safari visit to https://accounts.google.com/v3/signin/challenge/pk/presend?TL=APouJz5fd79Z_QU0-onAlnrDT3HYORCRvc6xbQbe-S4rW3qnTj8pVC_TF2mWK… |
| 03:30:56.122 | SafariHistory | Safari visit to https://accounts.google.com/v3/signin/challenge/ipp/verify?TL=APouJz5HMgOqtkGCO2nzPGAWpEvoJGMhIeExXzNvKoZgcycHLY_ViX8lixz_S… |
| 03:30:56.368 | SafariHistory | Safari visit to https://accounts.google.com/v3/signin/challenge/ipp/verify?TL=APouJz5HMgOqtkGCO2nzPGAWpEvoJGMhIeExXzNvKoZgcycHLY_ViX8lixz_S… |
| 03:30:56.756 | SafariHistory | Safari visit to https://accounts.google.com/v3/signin/challenge/selection?TL=APouJz47u5Hw6ttf9KasCqK911txTnVU4R3Y5TWYm2bigBFhz8Y2rtMOPY8GwR… |
| 03:30:56.900 | SafariHistory | Safari visit to https://accounts.google.com/v3/signin/challenge/selection?TL=APouJz47u5Hw6ttf9KasCqK911txTnVU4R3Y5TWYm2bigBFhz8Y2rtMOPY8GwR… |
| 03:30:57.441 | SafariHistory | Safari visit to https://www.google.com/search?q=crestview+austin+&ie=UTF-8&oe=UTF-8&hl=en-us&client=safari (ID: 6892, Visit ID: 21224) |
| 03:30:57.468 | SafariHistory | Safari visit to https://www.google.com/search?q=crestview+austin+&ie=UTF-8&oe=UTF-8&hl=en-us&client=safari (ID: 6892, Visit ID: 21225) |
| 03:30:58.003 | SafariHistory | Safari visit to https://www.google.com/search?q=disclosure+akient+movie+directors&ie=UTF-8&oe=UTF-8&hl=en-us&client=safari (ID: 6853, Visit… |
| 03:30:58.019 | SafariHistory | Safari visit to https://www.google.com/search?q=disclosure+akient+movie+directors&ie=UTF-8&oe=UTF-8&hl=en-us&client=safari (ID: 6853, Visit… |
| 03:30:58.428 | SafariHistory | Safari visit to https://www.google.com/search?q=disclosure+akient+movie+directors&ie=UTF-8&oe=UTF-8&hl=en-us&client=safari (ID: 6853, Visit… |
| 03:31:01.382 | SafariHistory | Safari visit to https://gmail.app.goo.gl/ (ID: 6992, Visit ID: 21229) |
| 03:31:07.006 ← ALERT | SafariHistory | Safari visit to http://gmail.com/ (ID: 2046, Visit ID: 21230) |
| 03:31:07.007 | SafariHistory | Safari visit to https://accounts.google.com/ServiceLogin?service=mail&passive=1209600&osid=1&continue=https://mail.google.com/mail/u/0/&fol… |
| 03:31:07.020 | SafariHistory | Safari visit to https://accounts.google.com/ServiceLogin (ID: 62, Visit ID: 21232) |
| 03:31:08.130 | SafariHistory | Safari visit to https://mail.google.com/accounts/SetOSID (ID: 6993, Visit ID: 21233) |
| 03:31:08.131 | SafariHistory | Safari visit to https://mail.google.com/mail/mu/?authuser=0 (ID: 927, Visit ID: 21234) |
| 03:31:08.503 | SafariHistory | Safari visit to https://mail.google.com/mail/mu/mp/683/?authuser=0 (ID: 2762, Visit ID: 21235) |
| 03:31:08.503 | SafariHistory | Safari visit to https://mail.google.com/mail/mu/mp/683/ (ID: 2289, Visit ID: 21236) |
| 03:31:09.350 | SafariHistory | Safari visit to https://mail.google.com/mail/mu/mp/683/#tl/Inbox (ID: 1432, Visit ID: 21237) |
| 03:33:38.192 | InteractionC | [com.google.Gmail] None - from Google (no-reply@accounts.google.com) to  (): |
| 03:33:38.242 | InteractionC | [com.google.Gmail] None - from Google (no-reply@accounts.google.com) to  (): |
| 03:38:04.276 | Datausage | appleaccountd/com.apple.datausage.appleid (Bundle ID: com.apple.datausage.appleid, ID: 575) WWAN IN: 40519.0, WWAN OUT: 26379.0 |
| 03:38:04.304 | Datausage | Preferences/com.apple.Preferences (Bundle ID: com.apple.Preferences, ID: 184) WWAN IN: 637642.0, WWAN OUT: 453314.0 |
| 03:38:07.308 | Datausage | appleaccountd/com.apple.datausage.appleid (Bundle ID: com.apple.datausage.appleid, ID: 575) |
| 03:38:20.962 | InteractionC | [com.google.Gmail] None - from Google (no-reply@accounts.google.com) to  (): |
| 03:38:20.994 | InteractionC | [com.google.Gmail] None - from Google (no-reply@accounts.google.com) to  (): |
| 03:38:21.687 | Datausage | NotificationService/com.google.GoogleMobile (Bundle ID: com.google.GoogleMobile, ID: 928) WWAN IN: 90108.0, WWAN OUT: 55894.0 |
| 03:38:28.336 | Datausage | trustd/com.apple.datausage.appleid (Bundle ID: com.apple.datausage.appleid, ID: 322) WWAN IN: 28968.0, WWAN OUT: 20303.0 |
| 03:39:00.130 | InteractionC | [org.whispersystems.signal] None - from Rob (+18303596439) to  (): |
| 03:39:00.291 | InteractionC | [org.whispersystems.signal] None - from Rob (+18303596439) to  (): |
| 03:39:37.266 | Datausage | rtcreportingd/com.apple.datausage.diagnostics (Bundle ID: com.apple.datausage.diagnostics, ID: 160) WWAN IN: 147763.0, WWAN OUT: 23512.0 |
| 03:39:38.588 | Datausage | identityservicesd/com.apple.datausage.appleid (Bundle ID: com.apple.datausage.appleid, ID: 62) WWAN IN: 199631.0, WWAN OUT: 169381.0 |
| 03:39:39.159 | Datausage | dataaccessd/com.apple.datausage.docsandsync (Bundle ID: com.apple.datausage.docsandsync, ID: 234) WWAN IN: 975542.0, WWAN OUT: 907530.0 |
| 03:39:40.325 | Datausage | findmydeviced/com.apple.datausage.findmyiphone (Bundle ID: com.apple.datausage.findmyiphone, ID: 218) WWAN IN: 122019.0, WWAN OUT: 232175.0 |
| 03:39:42.021 | Datausage | ind/com.apple.datausage.appleid (Bundle ID: com.apple.datausage.appleid, ID: 233) WWAN IN: 149560.0, WWAN OUT: 100525.0 |
| 03:39:42.022 | Datausage | dataaccessd/com.apple.mobilenotes (Bundle ID: com.apple.mobilenotes, ID: 565) WWAN IN: 27862.0, WWAN OUT: 10086.0 |
| 03:39:42.025 | Datausage | trustd/com.apple.datausage.findmyiphone (Bundle ID: com.apple.datausage.findmyiphone, ID: 279) WWAN IN: 26919.0, WWAN OUT: 30040.0 |
| 03:39:55.481 | Datausage | SignalNSE/org.whispersystems.signal (Bundle ID: org.whispersystems.signal, ID: 940) WWAN IN: 26170.0, WWAN OUT: 10687.0 |
| 03:39:55.482 | Datausage | SignalNSE/org.whispersystems.signal (Bundle ID: org.whispersystems.signal, ID: 940) |
| 03:40:15.082 | InteractionC | [org.whispersystems.signal] None - from Rob (+18303596439) to  (): |
| 03:40:15.112 | InteractionC | [org.whispersystems.signal] None - from Rob (+18303596439) to  (): |
| 03:40:31.350 | Datausage | cloudd/com.apple.datausage.security (Bundle ID: com.apple.datausage.security, ID: 196) WWAN IN: 258713.0, WWAN OUT: 456858.0 |
| 03:40:59.760 | InteractionC | [org.whispersystems.signal] None - from Rob (+18303596439) to  (): |
| 03:40:59.777 | InteractionC | [org.whispersystems.signal] None - from Rob (+18303596439) to  (): |
| 03:41:47.718 | InteractionC | [org.whispersystems.signal] None - from Rob (+18303596439) to  (): |
| 03:41:47.742 | InteractionC | [org.whispersystems.signal] None - from Rob (+18303596439) to  (): |
| 03:41:49.827 | InteractionC | [org.whispersystems.signal] None - from Rob (+18303596439) to  (): |
| 03:41:49.840 | InteractionC | [org.whispersystems.signal] None - from Rob (+18303596439) to  (): |
| 03:42:45.601 | InteractionC | [org.whispersystems.signal] None - from Rob (+18303596439) to  (): |
| 03:42:45.625 | InteractionC | [org.whispersystems.signal] None - from Rob (+18303596439) to  (): |
| 03:43:06.807 | InteractionC | [org.whispersystems.signal] None - from Rob (+18303596439) to  (): |
| 03:43:06.819 | InteractionC | [org.whispersystems.signal] None - from Rob (+18303596439) to  (): |
| 03:43:30.451 | Datausage | mediaplaybackd/com.reddit.Reddit (Bundle ID: com.reddit.Reddit, ID: 301) WWAN IN: 3974256.0, WWAN OUT: 238530.0 |
| 03:44:22.285 | InteractionC | [org.whispersystems.signal] None - from Rob (+18303596439) to  (): |
| 03:44:22.437 | InteractionC | [org.whispersystems.signal] None - from Rob (+18303596439) to  (): |
| 03:45:04.754 | Datausage | SignalNSE/org.whispersystems.signal (Bundle ID: org.whispersystems.signal, ID: 940) |
| 03:45:21.115 | InteractionC | [org.whispersystems.signal] None - from Rob (+18303596439) to  (): |
| 03:45:21.258 | InteractionC | [org.whispersystems.signal] None - from Rob (+18303596439) to  (): |

_(+33 low-signal backup-bookkeeping event(s) omitted: 33 Manifest)_

### `2026-05-24T07:14:07.398041+00:00` — MEDIUM — safari_history
> Redirect took less than a second! (0.12 milliseconds)
- **URL:** `http://tsyndicate.com/api/v1/direct/c8d8c6c128ca403f83f00029ebeb132c?categories=all`

**Correlated activity (±15 min, 50 event(s), excluding backup-internal churn):**

| Time | Module | Event |
| :--- | :--- | :--- |
| 07:05:04.000 | InteractionC | [com.apple.mobilemail] 8C493A40-947E-4B13-AFB5-28B7978937A2 - from Indeed (donotreply@match.indeed.com) to  (): |
| 07:07:11.620 | InteractionC | [com.apple.mobilemail] 8C493A40-947E-4B13-AFB5-28B7978937A2 - from Indeed Apply (indeedapply@indeed.com) to  (): |
| 07:07:11.643 | InteractionC | [com.apple.mobilemail] 8C493A40-947E-4B13-AFB5-28B7978937A2 - from WorkdaySystem_DoNotReply (thomsonreuters@myworkday.com) to  (): |
| 07:07:11.643 | InteractionC | [com.apple.mobilemail] 8C493A40-947E-4B13-AFB5-28B7978937A2 - from WorkdaySystem_DoNotReply (thomsonreuters@myworkday.com) to  (): |
| 07:07:11.643 | InteractionC | [com.apple.mobilemail] 8C493A40-947E-4B13-AFB5-28B7978937A2 - from Indeed Apply (indeedapply@indeed.com) to  (): |
| 07:07:11.643 | InteractionC | [com.apple.mobilemail] 8C493A40-947E-4B13-AFB5-28B7978937A2 - from Indeed (donotreply@match.indeed.com) to  (): |
| 07:14:04.329 | SafariHistory | Safari visit to https://out.reddit.com/t3_1tm47by?app_name=ios&token=AQAAX-sSanGLPrnsaMK0eSWj5n1oAF88PDw80oOWD9udjaqbSoJg&url=https%3A%2F%2… |
| 07:14:04.610 | SafariHistory | Safari visit to https://www.erome.com/a/Q43ktxSc (ID: 7000, Visit ID: 21244) |
| 07:14:05.000 | WebkitResourceLoadStatistics | Webkit resource loaded from eizzih.com by app in domain AppDomain-com.apple.mobilesafari |
| 07:14:05.000 | WebkitResourceLoadStatistics | Webkit resource loaded from coconts.com by app in domain AppDomain-com.apple.mobilesafari |
| 07:14:05.000 | WebkitResourceLoadStatistics | Webkit resource loaded from strpssts-ana.com by app in domain AppDomain-com.apple.mobilesafari |
| 07:14:05.000 | WebkitResourceLoadStatistics | Webkit resource loaded from doppiocdn.com by app in domain AppDomain-com.apple.mobilesafari |
| 07:14:05.000 | WebkitResourceLoadStatistics | Webkit resource loaded from strpst.com by app in domain AppDomain-com.apple.mobilesafari |
| 07:14:05.000 | WebkitResourceLoadStatistics | Webkit resource loaded from twinrdengine.com by app in domain AppDomain-com.apple.mobilesafari |
| 07:14:06.360 | SafariHistory | Safari visit to https://www.erome.com/o/p-3 (ID: 6455, Visit ID: 21245) |
| 07:14:06.368 | SafariHistory | Safari visit to https://www.erome.com/a/Q43ktxSc (ID: 7000, Visit ID: 21246) |
| 07:14:07.398 ← ALERT | SafariHistory | Safari visit to http://tsyndicate.com/api/v1/direct/c8d8c6c128ca403f83f00029ebeb132c?categories=all (ID: 6998, Visit ID: 21247) |
| 07:14:07.398 | SafariHistory | Safari visit to https://stripchat.com/Cutiepiespanks?abTest=gototheroom_AA18052026&abTestVariant=gototheroom_AA18052026_A_71&affiliateId=24… |
| 07:14:08.443 | SafariHistory | Safari visit to https://stripchat.com/Cutiepiespanks?abTest=gototheroom_AA18052026&abTestVariant=gototheroom_AA18052026_A_71&modelId=847398… |
| 07:14:35.000 | WebkitResourceLoadStatistics | Webkit resource loaded from chapturist.com by app in domain AppDomain-com.apple.mobilesafari |
| 07:14:35.658 | SafariHistory | Safari visit to https://www.erome.com/login/google (ID: 7004, Visit ID: 21250) |
| 07:14:35.658 | SafariHistory | Safari visit to https://accounts.google.com/v3/signin/accountchooser?client_id=3414710240-mnib3l8mejg8thkh83141uhgn86emt3a.apps.googleuserc… |
| 07:14:35.797 | SafariHistory | Safari visit to https://accounts.google.com/v3/signin/accountchooser?client_id=3414710240-mnib3l8mejg8thkh83141uhgn86emt3a.apps.googleuserc… |
| 07:14:38.737 | SafariHistory | Safari visit to https://accounts.google.com/ServiceLogin?app_domain=https%3A%2F%2Fwww.erome.com&authuser=0&client_id=3414710240-mnib3l8mejg… |
| 07:14:38.737 | SafariHistory | Safari visit to https://accounts.google.com/signin/oauth/id?authuser=0&part=AJi8hAPx5u5UlJw4HtSiwqZbZgZPNI1hh2f6q8loj_3MtW4V1mkQrifS3WMK6iH… |
| 07:14:39.033 | SafariHistory | Safari visit to https://accounts.google.com/signin/oauth/id?authuser=0&part=AJi8hAPx5u5UlJw4HtSiwqZbZgZPNI1hh2f6q8loj_3MtW4V1mkQrifS3WMK6iH… |
| 07:14:40.329 | SafariHistory | Safari visit to https://accounts.google.com/signin/oauth/consent?as=S1912714272%3A1779606875448755&authuser=0&client_id=3414710240-mnib3l8m… |
| 07:14:40.329 | SafariHistory | Safari visit to https://www.erome.com/ (ID: 7006, Visit ID: 21257) |
| 07:15:02.717 | SafariHistory | Safari visit to https://www.erome.com/login/google (ID: 7004, Visit ID: 21258) |
| 07:15:02.717 | SafariHistory | Safari visit to https://accounts.google.com/v3/signin/accountchooser?client_id=3414710240-mnib3l8mejg8thkh83141uhgn86emt3a.apps.googleuserc… |
| 07:15:02.864 | SafariHistory | Safari visit to https://accounts.google.com/v3/signin/accountchooser?client_id=3414710240-mnib3l8mejg8thkh83141uhgn86emt3a.apps.googleuserc… |
| 07:15:04.649 | SafariHistory | Safari visit to https://accounts.google.com/ServiceLogin?app_domain=https%3A%2F%2Fwww.erome.com&authuser=0&client_id=3414710240-mnib3l8mejg… |
| 07:15:04.650 | SafariHistory | Safari visit to https://accounts.google.com/signin/oauth/id?authuser=0&part=AJi8hANiwmu72S9wdvdJXdeFTn57T3zHjrfIoE2wkgnfhMwtmeL5gt8V03r76_u… |
| 07:15:04.764 | SafariHistory | Safari visit to https://accounts.google.com/signin/oauth/id?authuser=0&part=AJi8hANiwmu72S9wdvdJXdeFTn57T3zHjrfIoE2wkgnfhMwtmeL5gt8V03r76_u… |
| 07:15:06.042 | SafariHistory | Safari visit to https://accounts.google.com/signin/oauth/consent?as=S1681638601%3A1779606902471565&authuser=0&client_id=3414710240-mnib3l8m… |
| 07:15:06.042 | SafariHistory | Safari visit to https://www.erome.com/ (ID: 7006, Visit ID: 21265) |
| 07:15:11.065 | SafariHistory | Safari visit to https://www.erome.com/login/google (ID: 7004, Visit ID: 21266) |
| 07:15:11.065 | SafariHistory | Safari visit to https://accounts.google.com/v3/signin/accountchooser?client_id=3414710240-mnib3l8mejg8thkh83141uhgn86emt3a.apps.googleuserc… |
| 07:15:11.142 | SafariHistory | Safari visit to https://accounts.google.com/v3/signin/accountchooser?client_id=3414710240-mnib3l8mejg8thkh83141uhgn86emt3a.apps.googleuserc… |
| 07:15:13.250 | SafariHistory | Safari visit to https://accounts.google.com/ServiceLogin?app_domain=https%3A%2F%2Fwww.erome.com&authuser=0&client_id=3414710240-mnib3l8mejg… |
| 07:15:13.250 | SafariHistory | Safari visit to https://accounts.google.com/signin/oauth/id?authuser=0&part=AJi8hAOAVbqPQ6mDg10T0pRSqZGGz5dU81X4-IJbG-kMWNPddaXh25btHH1Tol5… |
| 07:15:13.315 | SafariHistory | Safari visit to https://accounts.google.com/signin/oauth/id?authuser=0&part=AJi8hAOAVbqPQ6mDg10T0pRSqZGGz5dU81X4-IJbG-kMWNPddaXh25btHH1Tol5… |
| 07:15:14.490 | SafariHistory | Safari visit to https://accounts.google.com/signin/oauth/consent?as=S-249788802%3A1779606910844061&authuser=0&client_id=3414710240-mnib3l8m… |
| 07:15:14.490 | SafariHistory | Safari visit to https://www.erome.com/ (ID: 7006, Visit ID: 21273) |
| 07:15:30.000 | WebkitResourceLoadStatistics | Webkit resource loaded from magsrv.com by app in domain AppDomain-com.apple.mobilesafari |
| 07:15:30.000 | WebkitResourceLoadStatistics | Webkit resource loaded from tsyndicate.com by app in domain AppDomain-com.apple.mobilesafari |
| 07:15:35.000 | WebkitResourceLoadStatistics | Webkit resource loaded from agego.com by app in domain AppDomain-com.apple.mobilesafari |
| 07:15:50.000 | WebkitResourceLoadStatistics | Webkit resource loaded from erome.com by app in domain AppDomain-com.apple.mobilesafari |
| 07:16:05.000 | WebkitResourceLoadStatistics | Webkit resource loaded from doppiostreams.com by app in domain AppDomain-com.apple.mobilesafari |
| 07:16:10.000 | WebkitResourceLoadStatistics | Webkit resource loaded from doppiocdn.net by app in domain AppDomain-com.apple.mobilesafari |

_(+18 low-signal backup-bookkeeping event(s) omitted: 18 Manifest)_

## Section 2 — Alerts with no timestamp (not correlatable)

- **LOW / global_preferences:** Lockdown mode disabled — `{'entry': 'LDMGlobalEnabled', 'value': False}`

## Section 3 — Timestamp-plausibility anomalies (new check; not an mvt alert type)

**1 event(s) timestamped AFTER the backup was taken** (`2026-05-28T11:23:38+00:00`) — impossible under normal device operation, worth investigating for clock tampering, anti-forensic timestomping, or an upstream parsing bug:

| Time | Module | Event | Description | Δ from backup |
| :--- | :--- | :--- | :--- | :--- |
| 2057-05-27T22:40:20.692377+00:00 | SafariBrowserState | tab | Notifications — OnlyFans - https://onlyfans.com/my/notifications | +31.0 yr |


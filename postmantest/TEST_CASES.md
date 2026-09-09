# API Test Cases - Nepal Travel Planner (Smart Travel Backend)

Complete Postman-style coverage, generated from a full audit of the FastAPI source.
Each test carries a permanent ID. 'Public' = no Authorization header. 
RATE LIMITS: register=3/min (429), login=10/min (429), chat POST=10/min (429).
429 is allowed as a transient status on calls that hit these limits. See README.

## 01 Setup & Health

| ID | Method | Endpoint | Case | Auth | Expected |
|---|---|---|---|---|---|
| SETUP-001 | `GET` | `/health` | Generate run identifiers | `public` |  |
| HEALTH-001 | `GET` | `/health` | Health check | `public` |  |
| SETUP-002 | `GET` | `/destinations/?limit=1` | Discover a destination id | `public` |  |
| SETUP-003 | `GET` | `/addresses/?limit=1` | Discover an address id | `public` |  |
| SETUP-004 | `GET` | `/attractions/?limit=1` | Discover an attraction id | `public` |  |
| SETUP-005 | `GET` | `/trekking-routes/?limit=1` | Discover a trekking-route id | `public` |  |
| SETUP-006 | `GET` | `/accommodations/?limit=1` | Discover an accommodation id | `public` |  |

## 02 Authentication

| ID | Method | Endpoint | Case | Auth | Expected |
|---|---|---|---|---|---|
| AUTH-001 | `POST` | `/auth/login` | Login seeded traveler (john@example.com) | `public` |  |
| AUTH-002 | `POST` | `/auth/login` | Login seeded admin (admin@example.com) | `public` |  |
| AUTH-003 | `POST` | `/auth/login` | Login seeded second user (ujjwal@gmail.com) | `public` |  |
| AUTH-004 | `POST` | `/auth/register` | Register new account (happy path) | `public` | **201** |
| AUTH-005 | `POST` | `/auth/register` | Register duplicate email | `public` | **409 or 429** |
| AUTH-006 | `POST` | `/auth/register` | Register - missing name | `public` | **422 or 429** |
| AUTH-007 | `POST` | `/auth/register` | Register - invalid email | `public` | **422 or 429** |
| AUTH-008 | `POST` | `/auth/register` | Register - missing password | `public` | **422 or 429** |
| AUTH-009 | `POST` | `/auth/register` | Register - invalid role | `public` | **422 or 429** |
| AUTH-010 | `POST` | `/auth/register` | Register - empty body | `public` | **422 or 429** |
| AUTH-011 | `POST` | `/auth/login` | Login - wrong password | `public` | **401** |
| AUTH-012 | `POST` | `/auth/login` | Login - invalid email format | `public` | **422** |
| AUTH-013 | `POST` | `/auth/login` | Login - missing password | `public` | **422** |
| AUTH-014 | `POST` | `/auth/login` | Login - empty body | `public` | **422** |
| AUTH-015 | `GET` | `/auth/me` | GET /auth/me (traveler) | `traveler` |  |
| AUTH-016 | `GET` | `/auth/me` | GET /auth/me - no token | `public` | **401** |
| AUTH-017 | `GET` | `/auth/me` | GET /auth/me - invalid token | `invalid` | **401** |
| AUTH-018 | `GET` | `/auth/me` | GET /auth/me - garbage id in sub (malformed JWT) | `invalid` | **401** |
| AUTH-019 | `PATCH` | `/auth/me` | PATCH /auth/me - update name | `traveler` |  |
| AUTH-020 | `PATCH` | `/auth/me` | PATCH /auth/me - empty name | `traveler` | **422** |
| AUTH-021 | `PATCH` | `/auth/me` | PATCH /auth/me - bad phone format | `traveler` | **422** |
| AUTH-022 | `PATCH` | `/auth/me` | PATCH /auth/me - no token | `public` | **401** |
| AUTH-023 | `PATCH` | `/auth/me` | PATCH /auth/me - body with unknown field ignored | `traveler` |  |
| AUTH-024 | `POST` | `/auth/change-password` | POST /auth/change-password - valid | `traveler` |  |
| AUTH-025 | `POST` | `/auth/login` | Login OLD password now fails | `public` | **401** |
| AUTH-026 | `POST` | `/auth/login` | Login NEW password works | `public` |  |
| AUTH-027 | `POST` | `/auth/change-password` | Change-password - wrong current password | `traveler` | **400** |
| AUTH-028 | `POST` | `/auth/change-password` | Change-password - missing fields | `traveler` | **422** |
| AUTH-029 | `POST` | `/auth/change-password` | Change-password - no token | `public` | **401** |
| AUTH-030 | `POST` | `/auth/forgot-password` | Forgot-password - existing email | `public` |  |
| AUTH-031 | `POST` | `/auth/forgot-password` | Forgot-password - nonexistent email (generic message) | `public` |  |
| AUTH-032 | `POST` | `/auth/forgot-password` | Forgot-password - bad email type | `public` | **422** |
| AUTH-033 | `POST` | `/auth/reset-password` | Reset-password - valid reset token | `public` |  |
| AUTH-034 | `POST` | `/auth/reset-password` | Reset-password - login token (wrong token type) | `traveler` | **400** |
| AUTH-035 | `POST` | `/auth/reset-password` | Reset-password - malformed token | `public` | **400** |
| AUTH-036 | `POST` | `/auth/reset-password` | Reset-password - missing fields | `public` | **422** |

## 03 Users

| ID | Method | Endpoint | Case | Auth | Expected |
|---|---|---|---|---|---|
| USER-001 | `GET` | `/users/?limit=5` | List users (public) | `public` |  |
| USER-002 | `GET` | `/users/` | List users - filter by email | `public` |  |
| USER-003 | `GET` | `/users/{{user_id}}` | Get user by id (public) | `public` |  |
| USER-004 | `GET` | `/users/00000000-0000-0000-0000-000000000000` | Get user - unknown id | `public` | **404** |
| USER-005 | `POST` | `/users/` | Admin create user | `admin` |  |
| USER-006 | `POST` | `/users/` | Create user as traveler (forbidden) | `traveler` | **403** |
| USER-007 | `POST` | `/users/` | Create user - no token | `public` | **401** |
| USER-008 | `POST` | `/users/` | Create user - duplicate email (admin) | `admin` | **409** |
| USER-009 | `POST` | `/users/` | Create user - weak password | `admin` | **422** |
| USER-010 | `POST` | `/users/` | Create user - bad email | `admin` | **422** |
| USER-011 | `PUT` | `/users/{{user_id}}` | Update own profile (owner) | `traveler` |  |
| USER-012 | `PUT` | `/users/{{created_user_id}}` | Update another user (forbidden) | `traveler` | **403** |
| USER-013 | `PUT` | `/users/{{user_id}}` | Update user - no token | `public` | **401** |
| USER-014 | `PUT` | `/users/{{user_id}}` | Update user - empty name | `traveler` | **422** |
| USER-015 | `DELETE` | `/users/{{created_user_id}}` | Admin delete the created user | `admin` |  |
| USER-016 | `GET` | `/users/{{created_user_id}}` | Deleted user is gone | `public` | **404** |
| USER-017 | `DELETE` | `/users/{{user_id}}` | Delete another user as non-admin | `second` | **403** |
| USER-018 | `DELETE` | `/users/00000000-0000-0000-0000-000000000000` | Delete unknown id (admin) | `admin` | **404** |

## 04 Destinations

| ID | Method | Endpoint | Case | Auth | Expected |
|---|---|---|---|---|---|
| DEST-001 | `GET` | `/destinations/` | List destinations | `public` |  |
| DEST-002 | `GET` | `/destinations/` | List - category=attraction | `public` |  |
| DEST-003 | `GET` | `/destinations/` | List - category=trek | `public` |  |
| DEST-004 | `GET` | `/destinations/` | List - rating_min=5 | `public` |  |
| DEST-005 | `GET` | `/destinations/` | List - rating_min out of range (0) | `public` | **422** |
| DEST-005b | `GET` | `/destinations/` | List - rating_min out of range (6) | `public` | **422** |
| DEST-006 | `GET` | `/destinations/` | List - limit=0 | `public` | **422** |
| DEST-006b | `GET` | `/destinations/` | List - offset negative | `public` | **422** |
| DEST-007 | `GET` | `/destinations/stats` | Destination stats | `public` |  |
| DEST-008 | `GET` | `/destinations/{{destination_id}}` | Get destination by id | `public` |  |
| DEST-009 | `GET` | `/destinations/00000000-0000-0000-0000-000000000000` | Get destination - unknown id | `public` | **404** |
| DEST-010 | `GET` | `/destinations/{{destination_id}}/budget-estimate` | Budget estimate (7 days, Foreign) | `public` |  |
| DEST-011 | `GET` | `/destinations/{{destination_id}}/budget-estimate` | Budget estimate - days=0 | `public` | **422** |
| DEST-012 | `GET` | `/destinations/{{destination_id}}/budget-estimate` | Budget estimate - days=61 | `public` | **422** |
| DEST-013 | `GET` | `/destinations/00000000-0000-0000-0000-000000000000/budget-estimate` | Budget estimate - unknown destination | `public` | **404** |
| DEST-014 | `POST` | `/destinations/` | Admin create destination (multipart + file) | `admin` | **201** |
| DEST-015 | `POST` | `/destinations/` | Create destination - no files | `admin` | **422** |
| DEST-016 | `POST` | `/destinations/` | Create destination as traveler (forbidden) | `traveler` | **403** |
| DEST-016b | `POST` | `/destinations/` | Create destination - no token | `public` | **401** |
| DEST-017 | `POST` | `/destinations/` | Create destination - bad file type | `admin` | **400** |
| DEST-018 | `POST` | `/destinations/` | Create destination - invalid best_time month | `admin` | **422** |
| DEST-018b | `POST` | `/destinations/` | Create destination - empty best_time | `admin` | **422** |
| DEST-018c | `POST` | `/destinations/` | Create destination - duplicate best_time months | `admin` | **422** |
| DEST-018d | `POST` | `/destinations/` | Create destination - latitude out of range | `admin` | **422** |
| DEST-018e | `POST` | `/destinations/` | Create destination - malformed destination JSON | `admin` | **422** |
| DEST-019 | `PUT` | `/destinations/{{new_destination_id}}` | Admin update destination | `admin` |  |
| DEST-019b | `PUT` | `/destinations/{{new_destination_id}}` | Update destination - bad file type | `admin` | **400** |
| DEST-020 | `PUT` | `/destinations/{{new_destination_id}}` | Update destination as traveler (forbidden) | `traveler` | **403** |
| DEST-020b | `PUT` | `/destinations/{{new_destination_id}}` | Update destination - no token | `public` | **401** |

## 05 Destination Content

| ID | Method | Endpoint | Case | Auth | Expected |
|---|---|---|---|---|---|
| DESTCONT-001 | `GET` | `/destinations/{{new_destination_id}}/content/` | Get destination content (auto-generates) | `public` |  |
| DESTCONT-002 | `GET` | `/destinations/00000000-0000-0000-0000-000000000000/content/` | Get content - unknown destination | `public` | **404** |
| DESTCONT-003 | `POST` | `/destinations/{{new_destination_id}}/content/highlights` | Admin create highlight | `admin` | **201** |
| DESTCONT-004 | `POST` | `/destinations/{{new_destination_id}}/content/highlights` | Create highlight - empty title | `admin` | **422** |
| DESTCONT-005 | `POST` | `/destinations/{{new_destination_id}}/content/highlights` | Create highlight as traveler (forbidden) | `traveler` | **403** |
| DESTCONT-006 | `POST` | `/destinations/{{new_destination_id}}/content/things-to-do` | Admin create thing-to-do | `admin` | **201** |
| DESTCONT-007 | `POST` | `/destinations/{{new_destination_id}}/content/things-to-do` | Create thing-to-do - missing title | `admin` | **422** |
| DESTCONT-008 | `POST` | `/destinations/{{new_destination_id}}/content/things-to-do` | Create thing-to-do as traveler (forbidden) | `traveler` | **403** |
| DESTCONT-009 | `POST` | `/destinations/{{new_destination_id}}/content/faqs` | Admin create FAQ | `admin` | **201** |
| DESTCONT-010 | `POST` | `/destinations/{{new_destination_id}}/content/faqs` | Create FAQ - empty answer | `admin` | **422** |
| DESTCONT-011 | `POST` | `/destinations/{{new_destination_id}}/content/regenerate` | Admin regenerate content | `admin` |  |
| DESTCONT-012 | `POST` | `/destinations/{{new_destination_id}}/content/regenerate` | Regenerate as traveler (forbidden) | `traveler` | **403** |
| DESTCONT-013 | `DELETE` | `/destinations/{{new_destination_id}}` | Cleanup: admin delete test destination | `admin` |  |
| DESTCONT-014 | `GET` | `/destinations/{{new_destination_id}}` | Deleted destination is gone | `public` | **404** |
| DESTCONT-015 | `DELETE` | `/destinations/00000000-0000-0000-0000-000000000000` | Delete destination - unknown id | `admin` | **404** |

## 06 Optimization

| ID | Method | Endpoint | Case | Auth | Expected |
|---|---|---|---|---|---|
| OPT-001 | `POST` | `/optimization/budget` | Budget - feasible plan | `public` |  |
| OPT-002 | `POST` | `/optimization/budget` | Budget - tiny budget may be infeasible (deficit present) | `public` |  |
| OPT-003 | `POST` | `/optimization/budget` | Budget - negative total_budget | `public` | **422** |
| OPT-004 | `POST` | `/optimization/budget` | Budget - party_size=0 | `public` | **422** |
| OPT-005 | `POST` | `/optimization/budget` | Budget - party_size=51 | `public` | **422** |
| OPT-006 | `POST` | `/optimization/budget` | Budget - days=0 | `public` | **422** |
| OPT-007 | `POST` | `/optimization/budget` | Budget - days=61 | `public` | **422** |
| OPT-008 | `POST` | `/optimization/budget` | Budget - missing destination_id | `public` | **422** |
| OPT-008b | `POST` | `/optimization/budget` | Budget - unknown destination | `public` | **404** |
| OPT-009 | `POST` | `/optimization/budget` | Budget - unknown fee_category falls back to Foreign | `public` |  |
| OPT-010 | `POST` | `/optimization/route` | Route - custom waypoints | `public` |  |
| OPT-011 | `POST` | `/optimization/route` | Route - custom waypoint missing latitude | `public` | **422** |
| OPT-012 | `POST` | `/optimization/route` | Route - unknown route_id | `public` | **404** |
| OPT-013 | `POST` | `/optimization/route` | Route - uses a DB trekking route | `public` |  |
| OPT-014 | `POST` | `/optimization/route` | Route - empty body (no ids, no points) | `public` | **500 or 422** |

## 07 Recommendations

| ID | Method | Endpoint | Case | Auth | Expected |
|---|---|---|---|---|---|
| REC-001 | `GET` | `/recommendations/?limit=5` | Get recommendations | `traveler` |  |
| REC-002 | `GET` | `/recommendations/?limit=5` | Get recommendations - no token | `public` | **401** |
| REC-003 | `GET` | `/recommendations/?limit=0` | Get recommendations - limit=0 | `traveler` | **422** |
| REC-004 | `GET` | `/recommendations/?limit=51` | Get recommendations - limit=51 | `traveler` | **422** |
| REC-005 | `GET` | `/recommendations/summary?limit=5` | Get recommendation summaries | `traveler` |  |
| REC-006 | `GET` | `/recommendations/preferences` | Get user preferences (defaults) | `traveler` |  |
| REC-007 | `POST` | `/recommendations/interaction` | Record interaction - view | `traveler` | **201** |
| REC-008 | `POST` | `/recommendations/interaction` | Record interaction - rating | `traveler` | **201** |
| REC-009 | `POST` | `/recommendations/interaction` | Record interaction - rating=6 invalid | `traveler` | **422** |
| REC-010 | `POST` | `/recommendations/interaction` | Record interaction - missing destination_id | `traveler` | **422** |
| REC-011 | `POST` | `/recommendations/interaction` | Record interaction - unknown destination | `traveler` | **400** |
| REC-012 | `POST` | `/recommendations/interaction` | Record interaction - no token | `public` | **401** |
| REC-013 | `POST` | `/recommendations/preferences` | Update preferences | `traveler` | **201** |
| REC-014 | `POST` | `/recommendations/preferences` | Update preferences - typical_duration=0 | `traveler` | **422** |
| REC-015 | `GET` | `/recommendations/preferences` | Preferences now reflect saved values | `traveler` |  |

## 08 Travel Info

| ID | Method | Endpoint | Case | Auth | Expected |
|---|---|---|---|---|---|
| TRAV-001 | `GET` | `/travel/weather/general` | Weather - general coordinates | `public` | **200 or 502** |
| TRAV-002 | `GET` | `/travel/weather/general` | Weather - latitude out of range | `public` | **422** |
| TRAV-003 | `GET` | `/travel/weather/general` | Weather - longitude out of range | `public` | **422** |
| TRAV-004 | `GET` | `/travel/weather/general` | Weather - days out of range | `public` | **422** |
| TRAV-005 | `GET` | `/travel/destinations/{{destination_id}}/weather` | Weather - destination | `public` | **200 or 502** |
| TRAV-006 | `GET` | `/travel/destinations/00000000-0000-0000-0000-000000000000/weather` | Weather - unknown destination | `public` | **404** |
| TRAV-007 | `GET` | `/travel/directions` | Directions - valid coords | `public` | **200 or 502 or 503** |
| TRAV-008 | `GET` | `/travel/directions` | Directions - missing coords | `public` | **422** |
| TRAV-009 | `GET` | `/travel/destinations/{{destination_id}}/flights` | Flights - destination | `public` |  |
| TRAV-010 | `GET` | `/travel/destinations/00000000-0000-0000-0000-000000000000/flights` | Flights - unknown destination | `public` | **404** |
| TRAV-011 | `GET` | `/travel/destinations/{{destination_id}}/map` | Map - destination GeoJSON | `public` |  |
| TRAV-012 | `GET` | `/travel/destinations/00000000-0000-0000-0000-000000000000/map` | Map - unknown destination | `public` | **404** |
| TRAV-013 | `GET` | `/travel/destinations/{{destination_id}}/nearby` | Nearby - default limit | `public` |  |
| TRAV-014 | `GET` | `/travel/destinations/{{destination_id}}/nearby` | Nearby - limit out of range | `public` | **422** |
| TRAV-015 | `GET` | `/travel/destinations/00000000-0000-0000-0000-000000000000/nearby` | Nearby - unknown destination | `public` | **404** |

## 09 Chat

| ID | Method | Endpoint | Case | Auth | Expected |
|---|---|---|---|---|---|
| CHAT-001 | `POST` | `/chat/` | Chat - greeting | `traveler` |  |
| CHAT-002 | `POST` | `/chat/` | Chat - Kathmandu question (Nepal scope) | `traveler` |  |
| CHAT-003 | `POST` | `/chat/` | Chat - follow-up (multi-turn) | `traveler` |  |
| CHAT-004 | `POST` | `/chat/` | Chat - trekking in autumn | `traveler` |  |
| CHAT-005 | `POST` | `/chat/` | Chat - out-of-scope country stays Nepal-focused | `traveler` |  |
| CHAT-006 | `POST` | `/chat/` | Chat - with user_profile | `traveler` |  |
| CHAT-007 | `POST` | `/chat/` | Chat - empty body (missing message) | `traveler` | **422** |
| CHAT-008 | `POST` | `/chat/` | Chat - no token | `public` | **401** |
| CHAT-009 | `GET` | `/chat/conversations` | List conversations | `traveler` |  |
| CHAT-010 | `GET` | `/chat/conversations/{{conversation_id}}` | Get conversation | `traveler` |  |
| CHAT-011 | `GET` | `/chat/conversations/00000000-0000-0000-0000-000000000000` | Get conversation - unknown id | `traveler` | **404** |
| CHAT-012 | `GET` | `/chat/conversations/{{conversation_id}}` | Get conversation - other user's | `second` | **404** |
| CHAT-013 | `GET` | `/chat/conversations` | Get conversations - no token | `public` | **401** |
| CHAT-014 | `DELETE` | `/chat/conversations/00000000-0000-0000-0000-000000000000` | Delete conversation - unknown id | `traveler` | **404** |
| CHAT-015 | `DELETE` | `/chat/conversations/{{conversation_id}}` | Delete conversation - other user's | `second` | **404** |
| CHAT-016 | `DELETE` | `/chat/conversations/{{conversation_id}}` | Delete conversation - owner | `traveler` |  |

## 10 Activity Logs

| ID | Method | Endpoint | Case | Auth | Expected |
|---|---|---|---|---|---|
| ALOG-001 | `GET` | `/activity-logs/?limit=5` | List activity logs (public) | `public` |  |
| ALOG-002 | `GET` | `/activity-logs/` | List - type filter | `public` |  |
| ALOG-003 | `GET` | `/activity-logs/` | List - limit out of range | `public` | **422** |

## 11 Trip Plans

| ID | Method | Endpoint | Case | Auth | Expected |
|---|---|---|---|---|---|
| TRIP-001 | `POST` | `/trip-plans/` | Create trip plan | `traveler` | **201** |
| TRIP-002 | `GET` | `/trip-plans/` | List trip plans | `traveler` |  |
| TRIP-003 | `GET` | `/trip-plans/{{trip_id}}` | Get trip plan | `traveler` |  |
| TRIP-004 | `GET` | `/trip-plans/00000000-0000-0000-0000-000000000000` | Get trip plan - unknown id | `traveler` | **404** |
| TRIP-005 | `PATCH` | `/trip-plans/{{trip_id}}` | Update trip plan | `traveler` |  |
| TRIP-005b | `PATCH` | `/trip-plans/{{trip_id}}` | Update trip - no-op empty body | `traveler` |  |
| TRIP-006 | `POST` | `/trip-plans/` | Create trip - missing name | `traveler` | **422** |
| TRIP-006b | `POST` | `/trip-plans/` | Create trip - name not a string | `traveler` | **422** |
| TRIP-007 | `POST` | `/trip-plans/` | Create trip - no token | `public` | **401** |
| TRIP-008 | `GET` | `/trip-plans/{{trip_b_id}}` | Get trip - other user's plan | `traveler` | **404** |
| TRIP-009 | `POST` | `/trip-plans/{{trip_b_id}}/messages` | POST message - other user's plan | `traveler` | **404** |
| TRIP-010 | `GET` | `/trip-plans/{{trip_id}}/messages` | GET messages (empty) | `traveler` |  |
| TRIP-011 | `POST` | `/trip-plans/{{trip_id}}/messages` | Send trip message (LLM) | `traveler` |  |
| TRIP-012 | `POST` | `/trip-plans/{{trip_id}}/messages` | Send follow-up trip message | `traveler` |  |
| TRIP-013 | `POST` | `/trip-plans/{{trip_id}}/messages` | Send trip message - missing message | `traveler` | **422** |
| TRIP-014 | `POST` | `/trip-plans/{{trip_id}}/messages` | Send trip message - no token | `public` | **401** |
| TRIP-015 | `GET` | `/trip-plans/{{trip_id}}/messages` | GET messages after sending | `traveler` |  |
| TRIP-016 | `GET` | `/trip-plans/{{trip_id}}/edits` | GET edits list | `traveler` |  |
| TRIP-017 | `POST` | `/trip-plans/{{trip_id}}/recommendations` | Add recommendation | `traveler` | **201** |
| TRIP-018 | `POST` | `/trip-plans/{{trip_id}}/recommendations` | Add recommendation - missing title | `traveler` | **422** |
| TRIP-019 | `POST` | `/trip-plans/{{trip_id}}/recommendations` | Add recommendation - no token | `public` | **401** |
| TRIP-020 | `GET` | `/trip-plans/{{trip_id}}/recommendations` | List recommendations | `traveler` |  |
| TRIP-021 | `POST` | `/trip-plans/{{trip_id}}/accept` | Accept trip plan | `traveler` |  |
| TRIP-022 | `POST` | `/trip-plans/{{trip_id}}/generate` | Generate itinerary | `traveler` |  |
| TRIP-023 | `POST` | `/trip-plans/{{trip_id}}/generate` | Generate - no token | `public` | **401** |
| TRIP-010b | `POST` | `/trip-plans/` | Create second-user trip plan | `second` | **201** |
| TRIP-024 | `DELETE` | `/trip-plans/{{trip_b_id}}` | Delete second-user trip (owner) | `second` |  |
| TRIP-025 | `GET` | `/trip-plans/{{trip_b_id}}` | Deleted second-user trip is gone | `second` | **404** |
| TRIP-026 | `DELETE` | `/trip-plans/{{trip_id}}` | Delete trip - no token | `public` | **401** |
| TRIP-027 | `DELETE` | `/trip-plans/{{trip_id}}` | Delete trip plan (owner cleanup) | `traveler` |  |
| TRIP-028 | `GET` | `/trip-plans/{{trip_id}}` | Deleted trip is gone | `traveler` | **404** |

## 12 User Trips

| ID | Method | Endpoint | Case | Auth | Expected |
|---|---|---|---|---|---|
| UTRI-001 | `POST` | `/user-trips/` | Create user trip | `traveler` | **201** |
| UTRI-002 | `GET` | `/user-trips/?limit=5` | List user trips (public) | `public` |  |
| UTRI-003 | `GET` | `/user-trips/mine` | List my trips | `traveler` |  |
| UTRI-004 | `GET` | `/user-trips/{{user_trip_id}}` | Get user trip (public) | `public` |  |
| UTRI-005 | `GET` | `/user-trips/00000000-0000-0000-0000-000000000000` | Get user trip - unknown id | `public` | **404** |
| UTRI-006 | `GET` | `/user-trips/mine` | List my trips - no token | `public` | **401** |
| UTRI-007 | `PUT` | `/user-trips/{{user_trip_id}}` | Update own user trip | `traveler` |  |
| UTRI-008 | `PUT` | `/user-trips/{{user_trip_id}}` | Update other user's trip (forbidden) | `second` | **403** |
| UTRI-009 | `PUT` | `/user-trips/{{user_trip_id}}` | Update - no token | `public` | **401** |
| UTRI-010 | `POST` | `/user-trips/` | Create - invalid pace_type | `traveler` | **422** |
| UTRI-011 | `POST` | `/user-trips/` | Create - invalid budget_type | `traveler` | **422** |
| UTRI-012 | `POST` | `/user-trips/` | Create - missing destination_id | `traveler` | **422** |
| UTRI-013 | `POST` | `/user-trips/` | Create - no token | `public` | **401** |
| UTRI-013b | `POST` | `/user-trips/` | Create - invalid date format | `traveler` | **422** |
| UTRI-014 | `POST` | `/user-trips/` | Create second (disposable) trip for deletion test | `traveler` | **201** |
| UTRI-015 | `DELETE` | `/user-trips/{{user_trip_del_id}}` | Delete other user's trip (forbidden) | `second` | **403** |
| UTRI-016 | `DELETE` | `/user-trips/{{user_trip_del_id}}` | Delete own disposable trip | `traveler` |  |
| UTRI-017 | `GET` | `/user-trips/{{user_trip_del_id}}` | Deleted trip is gone | `public` | **404** |
| UTRI-018 | `DELETE` | `/user-trips/{{user_trip_id}}` | Delete - no token | `public` | **401** |

## 13 Itineraries

| ID | Method | Endpoint | Case | Auth | Expected |
|---|---|---|---|---|---|
| ITIN-001 | `POST` | `/itineraries/` | Create itinerary for own user trip | `traveler` | **201** |
| ITIN-002 | `POST` | `/itineraries/` | Create itinerary - day_number=0 | `traveler` | **422** |
| ITIN-003 | `POST` | `/itineraries/` | Create itinerary - other user's trip (forbidden) | `second` | **403** |
| ITIN-004 | `POST` | `/itineraries/` | Create itinerary - no token | `public` | **401** |
| ITIN-005 | `GET` | `/itineraries/?limit=5` | List itineraries | `public` |  |
| ITIN-006 | `GET` | `/itineraries/{{itinerary_id}}` | Get itinerary | `public` |  |
| ITIN-007 | `GET` | `/itineraries/00000000-0000-0000-0000-000000000000` | Get itinerary - unknown id | `public` | **404** |
| ITIN-008 | `PUT` | `/itineraries/{{itinerary_id}}` | Update own itinerary | `traveler` |  |
| ITIN-009 | `PUT` | `/itineraries/{{itinerary_id}}` | Update itinerary - other user (forbidden) | `second` | **403** |
| ITIN-010 | `PUT` | `/itineraries/{{itinerary_id}}` | Update itinerary - day_number=0 | `traveler` | **422** |
| ITIN-011 | `DELETE` | `/itineraries/{{itinerary_id}}` | Delete itinerary - other user (forbidden) | `second` | **403** |
| ITIN-012 | `DELETE` | `/itineraries/{{itinerary_id}}` | Delete own itinerary | `traveler` |  |

## 14 Reviews

| ID | Method | Endpoint | Case | Auth | Expected |
|---|---|---|---|---|---|
| REVIEW-001 | `POST` | `/reviews/` | Create review | `traveler` | **201** |
| REVIEW-002 | `POST` | `/reviews/` | Create duplicate review (same destination) | `traveler` | **409** |
| REVIEW-003 | `POST` | `/reviews/` | Create review - rating=0 | `traveler` | **422** |
| REVIEW-003b | `POST` | `/reviews/` | Create review - rating=6 | `traveler` | **422** |
| REVIEW-004 | `POST` | `/reviews/` | Create review - missing destination | `traveler` | **422** |
| REVIEW-005 | `POST` | `/reviews/` | Create review - comment too long | `traveler` | **422** |
| REVIEW-006 | `GET` | `/reviews/?limit=5` | List reviews | `public` |  |
| REVIEW-007 | `GET` | `/reviews/{{review_id}}` | Get review | `public` |  |
| REVIEW-008 | `GET` | `/reviews/00000000-0000-0000-0000-000000000000` | Get review - unknown id | `public` | **404** |
| REVIEW-009 | `PUT` | `/reviews/{{review_id}}` | Update own review | `traveler` |  |
| REVIEW-010 | `PUT` | `/reviews/{{review_id}}` | Update review - other user (forbidden) | `second` | **403** |
| REVIEW-011 | `PUT` | `/reviews/{{review_id}}` | Update review - rating out of range | `traveler` | **422** |
| REVIEW-012 | `DELETE` | `/reviews/{{review_id}}` | Delete review - other user (forbidden) | `second` | **403** |
| REVIEW-013 | `DELETE` | `/reviews/{{review_id}}` | Delete own review | `traveler` |  |
| REVIEW-014 | `GET` | `/reviews/{{review_id}}` | Deleted review is gone | `public` | **404** |

## 15 Saved Destinations

| ID | Method | Endpoint | Case | Auth | Expected |
|---|---|---|---|---|---|
| SAVED-001 | `POST` | `/saved-destinations/` | Save destination | `traveler` | **201** |
| SAVED-002 | `POST` | `/saved-destinations/` | Save duplicate is idempotent | `traveler` | **201** |
| SAVED-003 | `POST` | `/saved-destinations/` | Save - missing destination | `traveler` | **422** |
| SAVED-004 | `GET` | `/saved-destinations/?limit=5` | List saved destinations | `public` |  |
| SAVED-005 | `GET` | `/saved-destinations/mine` | List my saved destinations | `traveler` |  |
| SAVED-006 | `GET` | `/saved-destinations/mine` | List mine - no token | `public` | **401** |
| SAVED-007 | `GET` | `/saved-destinations/{{saved_id}}` | Get saved destination | `public` |  |
| SAVED-008 | `GET` | `/saved-destinations/00000000-0000-0000-0000-000000000000` | Get saved destination - unknown id | `public` | **404** |
| SAVED-009 | `DELETE` | `/saved-destinations/{{saved_id}}` | Delete - other user (forbidden) | `second` | **403** |
| SAVED-010 | `DELETE` | `/saved-destinations/{{saved_id}}` | Delete own saved destination | `traveler` |  |
| SAVED-011 | `GET` | `/saved-destinations/{{saved_id}}` | Deleted saved destination is gone | `public` | **404** |

## 16 Photos

| ID | Method | Endpoint | Case | Auth | Expected |
|---|---|---|---|---|---|
| PHOTO-001 | `POST` | `/photos/json` | Create photo (JSON) | `traveler` | **201** |
| PHOTO-002 | `POST` | `/photos/json` | Create photo (JSON) - minimal (image_url defaults '') | `traveler` | **201** |
| PHOTO-003 | `POST` | `/photos/json` | Create photo - unknown destination (FK) | `traveler` | **500 or 400 or 422** |
| PHOTO-004 | `POST` | `/photos/` | Create photo (multipart upload) | `traveler` | **201** |
| PHOTO-005 | `POST` | `/photos/` | Create upload - bad file type | `traveler` | **400** |
| PHOTO-005b | `POST` | `/photos/` | Upload - missing file | `traveler` | **422** |
| PHOTO-006 | `POST` | `/photos/` | Upload - no token | `public` | **401** |
| PHOTO-007 | `GET` | `/photos/?limit=5` | List photos | `public` |  |
| PHOTO-008 | `GET` | `/photos/{{photo_id}}` | Get photo | `public` |  |
| PHOTO-009 | `GET` | `/photos/00000000-0000-0000-0000-000000000000` | Get photo - unknown id | `public` | **404** |
| PHOTO-010 | `PUT` | `/photos/{{photo_id}}` | Update own photo | `traveler` |  |
| PHOTO-011 | `PUT` | `/photos/{{photo_id}}` | Update photo - other user (forbidden) | `second` | **403** |
| PHOTO-012 | `DELETE` | `/photos/{{photo_id}}` | Delete photo - other user (forbidden) | `second` | **403** |
| PHOTO-013 | `DELETE` | `/photos/{{photo_id}}` | Delete own photo | `traveler` |  |

## 18 Admin Dashboard

| ID | Method | Endpoint | Case | Auth | Expected |
|---|---|---|---|---|---|
| ADMIN-001 | `GET` | `/admin/dashboard` | Admin dashboard | `admin` |  |
| ADMIN-002 | `GET` | `/admin/dashboard` | Admin dashboard as traveler (forbidden) | `traveler` | **403** |
| ADMIN-003 | `GET` | `/admin/dashboard` | Admin dashboard - no token | `public` | **401** |

## 17 Content Management - Addresses

| ID | Method | Endpoint | Case | Auth | Expected |
|---|---|---|---|---|---|
| ADDR-001 | `GET` | `/addresses/?limit=5` | List addresses | `public` |  |
| ADDR-002 | `POST` | `/addresses/` | Admin create address | `admin` |  |
| ADDR-003 | `POST` | `/addresses/` | Create address as traveler (forbidden) | `traveler` | **403** |
| ADDR-004 | `POST` | `/addresses/` | Create address - missing province | `admin` | **422** |
| ADDR-005 | `POST` | `/addresses/` | Create address - latitude out of range | `admin` | **422** |
| ADDR-006 | `POST` | `/addresses/` | Create address - altitude zero | `admin` | **422** |
| ADDR-007 | `GET` | `/addresses/{{address_new_id}}` | Get address by id | `public` |  |
| ADDR-008 | `GET` | `/addresses/00000000-0000-0000-0000-000000000000` | Get address - unknown id | `public` | **404** |
| ADDR-009 | `PUT` | `/addresses/{{address_new_id}}` | Admin update address | `admin` |  |
| ADDR-010 | `PUT` | `/addresses/{{address_new_id}}` | Update address as traveler (forbidden) | `traveler` | **403** |
| ADDR-011 | `DELETE` | `/addresses/{{address_new_id}}` | Admin delete address | `admin` |  |
| ADDR-012 | `DELETE` | `/addresses/00000000-0000-0000-0000-000000000000` | Delete address - unknown id | `admin` | **404** |

## 17 Content Management - Accommodations

| ID | Method | Endpoint | Case | Auth | Expected |
|---|---|---|---|---|---|
| ACCOM-001 | `GET` | `/accommodations/?limit=5` | List accommodations | `public` |  |
| ACCOM-002 | `POST` | `/accommodations/` | Admin create accommodation | `admin` | **201** |
| ACCOM-003 | `POST` | `/accommodations/` | Create as traveler (forbidden) | `traveler` | **403** |
| ACCOM-004 | `POST` | `/accommodations/` | Create - missing budget_price | `admin` | **422** |
| ACCOM-005 | `POST` | `/accommodations/` | Create - negative price | `admin` | **422** |
| ACCOM-006 | `GET` | `/accommodations/{{accommodation_new_id}}` | Get by id | `public` |  |
| ACCOM-007 | `GET` | `/accommodations/00000000-0000-0000-0000-000000000000` | Get - unknown id | `public` | **404** |
| ACCOM-008 | `PUT` | `/accommodations/{{accommodation_new_id}}` | Admin update | `admin` |  |
| ACCOM-009 | `DELETE` | `/accommodations/{{accommodation_new_id}}` | Admin delete | `admin` |  |

## 17 Content Management - Attractions

| ID | Method | Endpoint | Case | Auth | Expected |
|---|---|---|---|---|---|
| ATTR-001 | `GET` | `/attractions/?limit=5` | List attractions | `public` |  |
| ATTR-002 | `POST` | `/attractions/` | Admin create attraction | `admin` |  |
| ATTR-003 | `POST` | `/attractions/` | Create as traveler (forbidden) | `traveler` | **403** |
| ATTR-004 | `POST` | `/attractions/` | Create - missing attraction_types | `admin` | **422** |
| ATTR-005 | `POST` | `/attractions/` | Create - empty attraction_types | `admin` |  |
| ATTR-006 | `GET` | `/attractions/{{attraction_new_id}}` | Get by id | `public` |  |
| ATTR-007 | `PUT` | `/attractions/{{attraction_new_id}}` | Admin update | `admin` |  |
| ATTR-008 | `DELETE` | `/attractions/{{attraction_new_id}}` | Admin delete | `admin` |  |

## 17 Content Management - Blogs

| ID | Method | Endpoint | Case | Auth | Expected |
|---|---|---|---|---|---|
| BLOG-001 | `GET` | `/blogs/?limit=5` | List blogs | `public` |  |
| BLOG-002 | `POST` | `/blogs/` | Admin create blog | `admin` | **201** |
| BLOG-003 | `POST` | `/blogs/` | Create - missing content | `admin` | **422** |
| BLOG-004 | `POST` | `/blogs/` | Create - empty title | `admin` | **422** |
| BLOG-005 | `POST` | `/blogs/` | Create as traveler (forbidden) | `traveler` | **403** |
| BLOG-006 | `GET` | `/blogs/{{blog_id}}` | Get by id | `public` |  |
| BLOG-007 | `GET` | `/blogs/by-slug/{{blog_slug}}` | Get by slug | `public` |  |
| BLOG-008 | `GET` | `/blogs/by-slug/nonexistent-slug-{{uniq}}` | Get by slug - unknown | `public` | **404** |
| BLOG-009 | `GET` | `/blogs/by-category/trekking` | Get by category | `public` |  |
| BLOG-010 | `GET` | `/blogs/by-category/nonexistent-{{uniq}}` | Get by category - no results | `public` |  |
| BLOG-011 | `GET` | `/blogs/00000000-0000-0000-0000-000000000000` | Get - unknown id | `public` | **404** |
| BLOG-012 | `PUT` | `/blogs/{{blog_id}}` | Admin update | `admin` |  |
| BLOG-013 | `DELETE` | `/blogs/{{blog_id}}` | Admin delete | `admin` |  |
| BLOG-014 | `GET` | `/blogs/{{blog_id}}` | Deleted blog is gone | `public` | **404** |

## 17 Content Management - Entry Fees

| ID | Method | Endpoint | Case | Auth | Expected |
|---|---|---|---|---|---|
| ENTRY-001 | `GET` | `/entry-fees/?limit=5` | List entry fees | `public` |  |
| ENTRY-002 | `POST` | `/entry-fees/` | Admin create entry fee | `admin` | **201** |
| ENTRY-003 | `POST` | `/entry-fees/` | Create as traveler (forbidden) | `traveler` | **403** |
| ENTRY-004 | `POST` | `/entry-fees/` | Create - invalid category | `admin` | **422** |
| ENTRY-005 | `POST` | `/entry-fees/` | Create - negative price | `admin` | **422** |
| ENTRY-006 | `GET` | `/entry-fees/{{entry_fee_id}}` | Get by id | `public` |  |
| ENTRY-007 | `GET` | `/entry-fees/00000000-0000-0000-0000-000000000000` | Get - unknown id | `public` | **404** |
| ENTRY-008 | `PUT` | `/entry-fees/{{entry_fee_id}}` | Admin update | `admin` |  |
| ENTRY-009 | `DELETE` | `/entry-fees/{{entry_fee_id}}` | Admin delete | `admin` |  |

## 17 Content Management - Food Costs

| ID | Method | Endpoint | Case | Auth | Expected |
|---|---|---|---|---|---|
| FOOD-001 | `GET` | `/food_costs/?limit=5` | List food costs | `public` |  |
| FOOD-002 | `POST` | `/food_costs/` | Admin create food cost | `admin` | **201** |
| FOOD-003 | `POST` | `/food_costs/` | Create as traveler (forbidden) | `traveler` | **403** |
| FOOD-004 | `POST` | `/food_costs/` | Create - missing budget_price | `admin` | **422** |
| FOOD-005 | `GET` | `/food_costs/{{food_new_id}}` | Get by id | `public` |  |
| FOOD-006 | `GET` | `/food_costs/00000000-0000-0000-0000-000000000000` | Get - unknown id | `public` | **404** |
| FOOD-007 | `PUT` | `/food_costs/{{food_new_id}}` | Admin update | `admin` |  |
| FOOD-008 | `DELETE` | `/food_costs/{{food_new_id}}` | Admin delete | `admin` |  |

## 17 Content Management - Permits

| ID | Method | Endpoint | Case | Auth | Expected |
|---|---|---|---|---|---|
| PERMIT-001 | `GET` | `/permits/?limit=5` | List permits | `public` |  |
| PERMIT-002 | `POST` | `/permits/` | Admin create permit | `admin` | **201** |
| PERMIT-003 | `POST` | `/permits/` | Create as traveler (forbidden) | `traveler` | **403** |
| PERMIT-004 | `POST` | `/permits/` | Create - invalid category | `admin` | **422** |
| PERMIT-005 | `POST` | `/permits/` | Create - negative price | `admin` | **422** |
| PERMIT-006 | `GET` | `/permits/{{permit_new_id}}` | Get by id | `public` |  |
| PERMIT-007 | `GET` | `/permits/00000000-0000-0000-0000-000000000000` | Get - unknown id | `public` | **404** |
| PERMIT-008 | `PUT` | `/permits/{{permit_new_id}}` | Admin update | `admin` |  |
| PERMIT-009 | `DELETE` | `/permits/{{permit_new_id}}` | Admin delete | `admin` |  |

## 17 Content Management - Destination Itineraries

| ID | Method | Endpoint | Case | Auth | Expected |
|---|---|---|---|---|---|
| DITIN-001 | `GET` | `/destination-itineraries/?limit=5` | List destination itineraries | `public` |  |
| DITIN-002 | `GET` | `/destination-itineraries/by-destination/{{destination_id}}` | Get by destination | `public` |  |
| DITIN-003 | `GET` | `/destination-itineraries/by-destination/00000000-0000-0000-0000-000000000000` | Get by destination - unknown | `public` |  |
| DITIN-004 | `POST` | `/destination-itineraries/` | Admin create | `admin` | **201** |
| DITIN-005 | `POST` | `/destination-itineraries/` | Create - day_number=0 | `admin` | **422** |
| DITIN-006 | `POST` | `/destination-itineraries/` | Create as traveler (forbidden) | `traveler` | **403** |
| DITIN-007 | `GET` | `/destination-itineraries/{{ditin_new_id}}` | Get by id | `public` |  |
| DITIN-008 | `GET` | `/destination-itineraries/00000000-0000-0000-0000-000000000000` | Get - unknown id | `public` | **404** |
| DITIN-009 | `PUT` | `/destination-itineraries/{{ditin_new_id}}` | Admin update | `admin` |  |
| DITIN-010 | `DELETE` | `/destination-itineraries/{{ditin_new_id}}` | Admin delete | `admin` |  |

## 17 Content Management - Trekking Routes

| ID | Method | Endpoint | Case | Auth | Expected |
|---|---|---|---|---|---|
| TREK-001 | `GET` | `/trekking-routes/?limit=5` | List trekking routes | `public` |  |
| TREK-002 | `POST` | `/trekking-routes/` | Admin create trekking route | `admin` | **201** |
| TREK-003 | `POST` | `/trekking-routes/` | Create - invalid difficulty | `admin` | **422** |
| TREK-004 | `POST` | `/trekking-routes/` | Create as traveler (forbidden) | `traveler` | **403** |
| TREK-005 | `GET` | `/trekking-routes/{{trekking_route_new_id}}` | Get by id | `public` |  |
| TREK-006 | `GET` | `/trekking-routes/00000000-0000-0000-0000-000000000000` | Get - unknown id | `public` | **404** |
| TREK-007 | `PUT` | `/trekking-routes/{{trekking_route_new_id}}` | Admin update | `admin` |  |
| TREK-008 | `DELETE` | `/trekking-routes/{{trekking_route_new_id}}` | Admin delete | `admin` |  |

## 17 Content Management - Route Points

| ID | Method | Endpoint | Case | Auth | Expected |
|---|---|---|---|---|---|
| RTPT-001 | `GET` | `/route-points/?limit=5` | List route points | `public` |  |
| RTPT-002 | `POST` | `/route-points/` | Admin create route point | `admin` | **201** |
| RTPT-003 | `POST` | `/route-points/` | Create - missing address (route point requires address) | `admin` | **422** |
| RTPT-004 | `POST` | `/route-points/` | Create as traveler (forbidden) | `traveler` | **403** |
| RTPT-005 | `GET` | `/route-points/{{route_point_new_id}}` | Get by id | `public` |  |
| RTPT-006 | `GET` | `/route-points/00000000-0000-0000-0000-000000000000` | Get - unknown id | `public` | **404** |
| RTPT-007 | `PUT` | `/route-points/{{route_point_new_id}}` | Admin update | `admin` |  |
| RTPT-008 | `DELETE` | `/route-points/{{route_point_new_id}}` | Admin delete | `admin` |  |


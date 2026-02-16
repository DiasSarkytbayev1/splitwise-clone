# API Manual Testing Guide

Complete guide for testing the Splitwise Clone API with curl commands and example payloads.

## 📋 Prerequisites

- Application running on `http://localhost:8000`
- `curl` installed
- `jq` installed (optional, for parsing JSON responses)

## 🔧 Setup

Set base URL as environment variable:
```bash
export API_URL="http://localhost:8000"
```

---

## 1️⃣ Authentication

### Register a New User

**Endpoint:** `POST /auth/register`

```bash
curl -X POST "$API_URL/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Alice Smith",
    "email": "alice@example.com",
    "password": "password123"
  }'
```

**Expected Response (201):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user": {
    "id": "uuid-here",
    "name": "Alice Smith",
    "email": "alice@example.com",
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```

**Save the token:**
```bash
export TOKEN="eyJhbGciOiJIUzI1NiIs..."
```

### Register Additional Users

```bash
# Register Bob
curl -X POST "$API_URL/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Bob Johnson",
    "email": "bob@example.com",
    "password": "password123"
  }'

# Register Charlie
curl -X POST "$API_URL/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Charlie Brown",
    "email": "charlie@example.com",
    "password": "password123"
  }'
```

### Login

**Endpoint:** `POST /auth/login`

```bash
curl -X POST "$API_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "alice@example.com",
    "password": "password123"
  }'
```

**Save token:**
```bash
export TOKEN="<access_token_from_response>"
```

### Get Current User

**Endpoint:** `GET /auth/me`

```bash
curl -X GET "$API_URL/auth/me" \
  -H "Authorization: Bearer $TOKEN"
```

**Expected Response (200):**
```json
{
  "id": "user-uuid",
  "name": "Alice Smith",
  "email": "alice@example.com",
  "created_at": "2024-01-15T10:30:00Z"
}
```

---

## 2️⃣ Group Management

### Create a Group

**Endpoint:** `POST /groups`

```bash
curl -X POST "$API_URL/groups" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Weekend Trip to Paris",
    "type": "trip",
    "currency_code": "EUR",
    "cover_image": "https://example.com/paris.jpg"
  }'
```

**Expected Response (201):**
```json
{
  "id": "group-uuid",
  "name": "Weekend Trip to Paris",
  "type": "trip",
  "currency_code": "EUR",
  "cover_image": "https://example.com/paris.jpg",
  "invite_code": "ABC12345",
  "created_by": "user-uuid",
  "created_at": "2024-01-15T10:35:00Z"
}
```

**Save group ID:**
```bash
export GROUP_ID="<group-uuid-from-response>"
```

### List All Groups

**Endpoint:** `GET /groups`

```bash
curl -X GET "$API_URL/groups" \
  -H "Authorization: Bearer $TOKEN"
```

**Expected Response (200):**
```json
[
  {
    "id": "group-uuid",
    "name": "Weekend Trip to Paris",
    "type": "trip",
    "currency_code": "EUR",
    "cover_image": "https://example.com/paris.jpg",
    "invite_code": "ABC12345",
    "created_by": "user-uuid",
    "created_at": "2024-01-15T10:35:00Z"
  }
]
```

### Get Group by ID

**Endpoint:** `GET /groups/{id}`

```bash
curl -X GET "$API_URL/groups/$GROUP_ID" \
  -H "Authorization: Bearer $TOKEN"
```

### Get Group by Invite Code

**Endpoint:** `GET /groups/{code}`

```bash
curl -X GET "$API_URL/groups/ABC12345" \
  -H "Authorization: Bearer $TOKEN"
```

---

## 3️⃣ Group Members

### Get List of Members

**Endpoint:** `GET /groups/{group_id}/members`

```bash
curl -X GET "$API_URL/groups/$GROUP_ID/members" \
  -H "Authorization: Bearer $TOKEN"
```

**Expected Response (200):**
```json
[
  {
    "id": "member-uuid",
    "group_id": "group-uuid",
    "user_id": "alice-uuid",
    "joined_at": "2024-01-15T10:35:00Z",
    "user_name": "Alice Smith",
    "user_email": "alice@example.com"
  }
]
```

### Get Invite Code

**Endpoint:** `GET /groups/{group_id}/members/invite`

```bash
curl -X GET "$API_URL/groups/$GROUP_ID/members/invite" \
  -H "Authorization: Bearer $TOKEN"
```

**Expected Response (200):**
```json
{
  "invite_code": "ABC12345"
}
```

### Add Member by User ID

**Endpoint:** `POST /groups/{group_id}/members`

**First, get Bob's user ID from his token or registration response**

```bash
# Login as Bob to get his ID
BOB_TOKEN=$(curl -s -X POST "$API_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "bob@example.com",
    "password": "password123"
  }' | jq -r '.user.id')

export BOB_ID="$BOB_TOKEN"
```

**Then add Bob to the group (as Alice):**
```bash
curl -X POST "$API_URL/groups/$GROUP_ID/members" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "'"$BOB_ID"'"
  }'
```

### Add Member by Email

```bash
curl -X POST "$API_URL/groups/$GROUP_ID/members" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "charlie@example.com"
  }'
```

**Expected Response (201):**
```json
{
  "id": "member-uuid",
  "group_id": "group-uuid",
  "user_id": "charlie-uuid",
  "joined_at": "2024-01-15T10:40:00Z",
  "user_name": "Charlie Brown",
  "user_email": "charlie@example.com"
}
```

### Remove Member

**Endpoint:** `DELETE /groups/{group_id}/members/{user_id}`

```bash
curl -X DELETE "$API_URL/groups/$GROUP_ID/members/$BOB_ID" \
  -H "Authorization: Bearer $TOKEN"
```

**Expected Response (204 No Content)**

---

## 4️⃣ Expenses

### Create an Expense

**Endpoint:** `POST /groups/{group_id}/expenses`

**Note:** You need the user IDs of the payer and debtors. Use the IDs from member list.

```bash
# Save Alice's ID as payer
export ALICE_ID="<alice-user-uuid>"
export BOB_ID="<bob-user-uuid>"
export CHARLIE_ID="<charlie-user-uuid>"

curl -X POST "$API_URL/groups/$GROUP_ID/expenses" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Dinner at Italian Restaurant",
    "amount": 150.00,
    "payer_id": "'"$ALICE_ID"'",
    "category": "food",
    "splits": [
      {
        "debtor_id": "'"$BOB_ID"'",
        "creditor_id": "'"$ALICE_ID"'",
        "amount_owed": 50.00,
        "percentage": 33.33
      },
      {
        "debtor_id": "'"$CHARLIE_ID"'",
        "creditor_id": "'"$ALICE_ID"'",
        "amount_owed": 50.00,
        "percentage": 33.33
      },
      {
        "debtor_id": "'"$ALICE_ID"'",
        "creditor_id": "'"$ALICE_ID"'",
        "amount_owed": 50.00,
        "percentage": 33.34
      }
    ]
  }'
```

**Expected Response (201):**
```json
{
  "id": "expense-uuid",
  "group_id": "group-uuid",
  "payer_id": "alice-uuid",
  "description": "Dinner at Italian Restaurant",
  "amount": 150.00,
  "category": "food",
  "date": "2024-01-15T19:30:00Z",
  "created_at": "2024-01-15T19:30:00Z",
  "splits": [
    {
      "id": "split-uuid-1",
      "debtor_id": "bob-uuid",
      "creditor_id": "alice-uuid",
      "amount_owed": 50.00,
      "percentage": 33.33,
      "status": "pending"
    },
    {
      "id": "split-uuid-2",
      "debtor_id": "charlie-uuid",
      "creditor_id": "alice-uuid",
      "amount_owed": 50.00,
      "percentage": 33.33,
      "status": "pending"
    }
  ]
}
```

**Save expense ID and first split ID:**
```bash
export EXPENSE_ID="<expense-uuid-from-response>"
export SPLIT_ID="<first-split-uuid-from-response>"
```

### Create More Expenses

```bash
# Groceries (Bob pays)
curl -X POST "$API_URL/groups/$GROUP_ID/expenses" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Groceries for the trip",
    "amount": 85.50,
    "payer_id": "'"$BOB_ID"'",
    "category": "groceries",
    "splits": [
      {
        "debtor_id": "'"$ALICE_ID"'",
        "creditor_id": "'"$BOB_ID"'",
        "amount_owed": 28.50,
        "percentage": 33.33
      },
      {
        "debtor_id": "'"$CHARLIE_ID"'",
        "creditor_id": "'"$BOB_ID"'",
        "amount_owed": 28.50,
        "percentage": 33.33
      },
      {
        "debtor_id": "'"$BOB_ID"'",
        "creditor_id": "'"$BOB_ID"'",
        "amount_owed": 28.50,
        "percentage": 33.34
      }
    ]
  }'

# Transportation (Charlie pays)
curl -X POST "$API_URL/groups/$GROUP_ID/expenses" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Uber to airport",
    "amount": 45.00,
    "payer_id": "'"$CHARLIE_ID"'",
    "category": "transportation",
    "splits": [
      {
        "debtor_id": "'"$ALICE_ID"'",
        "creditor_id": "'"$CHARLIE_ID"'",
        "amount_owed": 15.00,
        "percentage": 33.33
      },
      {
        "debtor_id": "'"$BOB_ID"'",
        "creditor_id": "'"$CHARLIE_ID"'",
        "amount_owed": 15.00,
        "percentage": 33.33
      },
      {
        "debtor_id": "'"$CHARLIE_ID"'",
        "creditor_id": "'"$CHARLIE_ID"'",
        "amount_owed": 15.00,
        "percentage": 33.34
      }
    ]
  }'
```

### List Expenses (with pagination)

**Endpoint:** `GET /groups/{group_id}/expenses`

```bash
# First page (default: 50 items)
curl -X GET "$API_URL/groups/$GROUP_ID/expenses?page=1&limit=50" \
  -H "Authorization: Bearer $TOKEN"

# Custom pagination
curl -X GET "$API_URL/groups/$GROUP_ID/expenses?page=1&limit=10" \
  -H "Authorization: Bearer $TOKEN"
```

**Expected Response (200):**
```json
{
  "expenses": [
    {
      "id": "expense-uuid",
      "group_id": "group-uuid",
      "payer_id": "alice-uuid",
      "description": "Dinner at Italian Restaurant",
      "amount": 150.00,
      "category": "food",
      "date": "2024-01-15T19:30:00Z",
      "created_at": "2024-01-15T19:30:00Z",
      "splits": [...]
    }
  ],
  "total": 3,
  "page": 1,
  "limit": 50,
  "total_pages": 1
}
```

### Get Single Expense

**Endpoint:** `GET /expenses/{id}`

```bash
curl -X GET "$API_URL/expenses/$EXPENSE_ID" \
  -H "Authorization: Bearer $TOKEN"
```

### Create a Settlement

**Settlements are expenses with category="settlement"**

```bash
curl -X POST "$API_URL/groups/$GROUP_ID/expenses" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Bob pays back Alice",
    "amount": 50.00,
    "payer_id": "'"$BOB_ID"'",
    "category": "settlement",
    "splits": [
      {
        "debtor_id": "'"$ALICE_ID"'",
        "creditor_id": "'"$BOB_ID"'",
        "amount_owed": 50.00,
        "percentage": 100.00
      }
    ]
  }'
```

---

## 5️⃣ Debts

### List All Debts in a Group

**Endpoint:** `GET /groups/{group_id}/debts`

```bash
curl -X GET "$API_URL/groups/$GROUP_ID/debts" \
  -H "Authorization: Bearer $TOKEN"
```

**Expected Response (200):**
```json
[
  {
    "debtor_id": "bob-uuid",
    "creditor_id": "alice-uuid",
    "total_owed": 50.00
  },
  {
    "debtor_id": "charlie-uuid",
    "creditor_id": "alice-uuid",
    "total_owed": 50.00
  },
  {
    "debtor_id": "alice-uuid",
    "creditor_id": "bob-uuid",
    "total_owed": 28.50
  }
]
```

### Settle a Specific Debt

**Endpoint:** `POST /groups/{group_id}/debts/{debt_id}/settle`

**The debt_id is the split ID from an expense**

```bash
curl -X POST "$API_URL/groups/$GROUP_ID/debts/$SPLIT_ID/settle" \
  -H "Authorization: Bearer $TOKEN"
```

**Expected Response (200):**
```json
{
  "settled_count": 1,
  "message": "Debt of 50.00 settled successfully"
}
```

---

## 🔄 Complete Testing Flow

### Step-by-Step Test Scenario

```bash
# 1. Set base URL
export API_URL="http://localhost:8000"

# 2. Register three users
curl -s -X POST "$API_URL/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"name":"Alice","email":"alice@test.com","password":"pass123"}' > alice.json

curl -s -X POST "$API_URL/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"name":"Bob","email":"bob@test.com","password":"pass123"}' > bob.json

curl -s -X POST "$API_URL/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"name":"Charlie","email":"charlie@test.com","password":"pass123"}' > charlie.json

# 3. Extract tokens and IDs
export ALICE_TOKEN=$(cat alice.json | jq -r '.access_token')
export ALICE_ID=$(cat alice.json | jq -r '.user.id')
export BOB_ID=$(cat bob.json | jq -r '.user.id')
export CHARLIE_ID=$(cat charlie.json | jq -r '.user.id')

# 4. Alice creates a group
GROUP_RESPONSE=$(curl -s -X POST "$API_URL/groups" \
  -H "Authorization: Bearer $ALICE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Trip to Paris","type":"trip","currency_code":"EUR"}')

export GROUP_ID=$(echo $GROUP_RESPONSE | jq -r '.id')
export INVITE_CODE=$(echo $GROUP_RESPONSE | jq -r '.invite_code')

echo "Group created: $GROUP_ID"
echo "Invite code: $INVITE_CODE"

# 5. Alice adds Bob and Charlie
curl -s -X POST "$API_URL/groups/$GROUP_ID/members" \
  -H "Authorization: Bearer $ALICE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"user_id":"'"$BOB_ID"'"}' | jq '.'

curl -s -X POST "$API_URL/groups/$GROUP_ID/members" \
  -H "Authorization: Bearer $ALICE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"email":"charlie@test.com"}' | jq '.'

# 6. Alice creates an expense
EXPENSE_RESPONSE=$(curl -s -X POST "$API_URL/groups/$GROUP_ID/expenses" \
  -H "Authorization: Bearer $ALICE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "description":"Dinner",
    "amount":150.00,
    "payer_id":"'"$ALICE_ID"'",
    "category":"food",
    "splits":[
      {"debtor_id":"'"$BOB_ID"'","creditor_id":"'"$ALICE_ID"'","amount_owed":50.00,"percentage":33.33},
      {"debtor_id":"'"$CHARLIE_ID"'","creditor_id":"'"$ALICE_ID"'","amount_owed":50.00,"percentage":33.33}
    ]
  }')

echo "Expense created:"
echo $EXPENSE_RESPONSE | jq '.'

export SPLIT_ID=$(echo $EXPENSE_RESPONSE | jq -r '.splits[0].id')

# 7. List all expenses
echo "All expenses:"
curl -s -X GET "$API_URL/groups/$GROUP_ID/expenses?page=1&limit=10" \
  -H "Authorization: Bearer $ALICE_TOKEN" | jq '.'

# 8. View debts
echo "Current debts:"
curl -s -X GET "$API_URL/groups/$GROUP_ID/debts" \
  -H "Authorization: Bearer $ALICE_TOKEN" | jq '.'

# 9. Settle Bob's debt
echo "Settling Bob's debt..."
curl -s -X POST "$API_URL/groups/$GROUP_ID/debts/$SPLIT_ID/settle" \
  -H "Authorization: Bearer $ALICE_TOKEN" | jq '.'

# 10. View debts again
echo "Debts after settlement:"
curl -s -X GET "$API_URL/groups/$GROUP_ID/debts" \
  -H "Authorization: Bearer $ALICE_TOKEN" | jq '.'

# Cleanup
rm -f alice.json bob.json charlie.json
```

---

## 📱 Postman Collection Variables

If using Postman, set these variables:

```
BASE_URL: http://localhost:8000
TOKEN: <your-jwt-token>
GROUP_ID: <your-group-id>
ALICE_ID: <alice-user-id>
BOB_ID: <bob-user-id>
CHARLIE_ID: <charlie-user-id>
EXPENSE_ID: <expense-id>
SPLIT_ID: <split-id>
```

Then use `{{BASE_URL}}`, `{{TOKEN}}`, etc. in your requests.

---

## 🐛 Common Issues

### 401 Unauthorized
- Token expired or invalid
- Missing `Authorization: Bearer <token>` header

### 403 Forbidden
- User not a member of the group
- Trying to access resources you don't have permission for

### 404 Not Found
- Invalid ID
- Resource doesn't exist

### 409 Conflict
- Email already registered
- User already a member

### 422 Validation Error
- Invalid request body
- Missing required fields
- Invalid email format

---

## ✅ Verification Checklist

- [ ] Register multiple users
- [ ] Login and receive JWT token
- [ ] Access /auth/me with token
- [ ] Create a group
- [ ] List groups
- [ ] Get group by ID
- [ ] Get group by invite code
- [ ] Add members to group
- [ ] Get invite code
- [ ] List members
- [ ] Create expenses
- [ ] List expenses (with pagination)
- [ ] Get single expense
- [ ] Create settlement
- [ ] View debts
- [ ] Settle a debt
- [ ] View debts after settlement
- [ ] Remove a member

---

## 📚 API Documentation

Interactive documentation available at:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

---

## 🎯 Quick Test Commands

### Health Check
```bash
curl -X GET "$API_URL/"
```

### Register & Login Quick Test
```bash
# Register
curl -X POST "$API_URL/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"name":"Test User","email":"test@example.com","password":"test123"}'

# Login
curl -X POST "$API_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}'
```

---

**Happy Testing! 🎉**

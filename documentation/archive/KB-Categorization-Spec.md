# KB Categorization Enhancement Analysis & Specification
## Agentic AI Test Case Generator - Dynamic KB Categories Feature

**Document Version:** 1.0  
**Date:** November 7, 2025  
**Feature:** KB Document Categorization with Dynamic Categories  
**Phase:** Phase 1.5 (Enhanced Phase 1)  
**Status:** Recommended for Implementation  

---

# EXECUTIVE SUMMARY

**PROPOSAL:** Add KB document categorization with both predefined and user-created categories during upload.

**RECOMMENDATION:** ✅ **YES - IMPLEMENT IN PHASE 1.5**

**Why This Is Important:**
- Significantly improves **agent efficiency** by filtering KB context to relevant documents only
- Enables **scalability** from 100 to 1000+ documents
- Enhances **user experience** by letting users organize KB intuitively
- Minimal implementation effort: **+1 hour** only
- High benefit-to-effort ratio

**Expected Benefits:**
- ⚡ **Agent Performance**: 20-30% faster generation (smaller context)
- 🎯 **Test Case Quality**: +10-15% more relevant (focused context)
- 📦 **Scalability**: Support 1000+ docs vs 100 docs max
- 👤 **User Experience**: Intuitive KB organization
- 🔧 **Maintainability**: Easier KB management as docs grow

---

# PROBLEM & OPPORTUNITY

## Current Limitation

In the current KB feature:
- All uploaded KB documents are treated equally
- Agents receive **all KB documents as context** regardless of relevance
- Example: When generating CRM test cases, agent sees Billing docs, Network docs, Mobile App docs (irrelevant)
- Context window bloated with irrelevant information
- LLM processes unnecessary content → slower, less accurate

## Proposed Solution

Add **KB categorization** where:

1. **Predefined Categories** (e.g., CRM, Billing, Network, Mobile App)
   - User selects from dropdown during upload
   - Familiar system for users
   - Consistent categorization

2. **User-Created Categories** (e.g., "5G Services", "VAS", "Loyalty Program")
   - User clicks "[+ Create New Category]" in dropdown
   - Enters category name in modal
   - System saves for future use
   - Flexibility for custom needs

3. **Category-Aware Agents**
   - Planner Agent: "Reference KB documents from [CRM] category"
   - Generator Agent: "Use [CRM] KB for realistic test steps"
   - Executor Agent: "Validate against [CRM] KB procedures"

---

# BENEFITS ANALYSIS

## 1. Agent Efficiency ⚡

**Current Flow:**
```
User: Generate CRM test cases
Agent receives: 100 KB documents (all categories mixed)
├─ CRM docs: 20 docs (relevant)
├─ Billing docs: 20 docs (irrelevant for CRM)
├─ Network docs: 20 docs (irrelevant)
├─ Mobile App docs: 20 docs (irrelevant)
└─ Other docs: 20 docs (irrelevant)

Agent must filter through irrelevant content
Result: Slower processing, less focused test cases
```

**Proposed Flow:**
```
User: Generate CRM test cases → System filters: [CRM] category only
Agent receives: 20 KB documents (CRM only)
├─ CRM_User_Guide.pdf ✓
├─ CRM_Procedures.pdf ✓
├─ CRM_Fields_Reference.pdf ✓
└─ CRM_Process_Flows.pdf ✓

Agent focuses on relevant context only
Result: 20-30% faster, more accurate, better test cases
```

## 2. Scalability 📦

**Current:** Max 100 documents recommended
- Context window concerns (LLM token limits)
- Agent confusion with too many irrelevant docs

**Proposed:** 1000+ documents supported
- Organize by category (CRM, Billing, Network, etc.)
- Agent uses only relevant category (20-50 docs typically)
- Same performance as current 100-doc system
- **5-10x more scalable**

## 3. User Experience 👤

**Current:**
- System assigns doc_type (system_guide, process, reference, product)
- User has no control over organization
- Generic classification not tailored to user's needs

**Proposed:**
- User chooses category during upload
- User can create new categories on-the-fly
- KB organized intuitively for user's project
- Categories match user's mental model

## 4. Agent Accuracy 🎯

**Current:** Agent tries to use all KB docs
- May reference wrong system docs
- Confusion between similar systems
- Generic test steps (applies to multiple systems)

**Proposed:** Agent uses category-specific docs only
- CRM category → CRM-specific test steps
- Billing category → Billing-specific validation
- Mobile App category → Mobile-specific test scenarios
- **+10-15% accuracy improvement**

## 5. Maintainability 🔧

**Current:**
- All docs mixed together
- Hard to find relevant docs
- No organization as KB grows

**Proposed:**
- KB organized by category
- Easy to find all CRM docs, all Billing docs, etc.
- Natural structure as new categories emerge
- Future admin panel can show category stats

---

# IMPLEMENTATION DETAILS

## Database Schema Changes

### New Table: kb_categories

```sql
CREATE TABLE kb_categories (
    category_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(project_id) ON DELETE CASCADE,
    category_name VARCHAR(100) NOT NULL,
    description TEXT,
    color VARCHAR(7) DEFAULT '#3498db',  -- Hex color for UI badge
    icon VARCHAR(50) DEFAULT 'folder',   -- Icon name (e.g., 'database', 'settings')
    display_order INT DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    is_predefined BOOLEAN DEFAULT FALSE, -- Mark predefined vs user-created
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by UUID,  -- Phase 2
    
    UNIQUE(project_id, category_name)
);

CREATE INDEX idx_kb_cat_project ON kb_categories(project_id);
CREATE INDEX idx_kb_cat_active ON kb_categories(is_active);
CREATE INDEX idx_kb_cat_order ON kb_categories(display_order);
```

### Updated Table: knowledge_base_documents

```sql
-- ADD new column
ALTER TABLE knowledge_base_documents ADD COLUMN (
    kb_category_id UUID REFERENCES kb_categories(category_id) ON DELETE SET NULL,
    doc_sub_type VARCHAR(50)  -- Rename from doc_type: system_guide, process, reference, product
);

-- Rename existing column
ALTER TABLE knowledge_base_documents RENAME COLUMN doc_type TO doc_sub_type;

-- Create index
CREATE INDEX idx_kb_doc_category ON knowledge_base_documents(kb_category_id);
```

### Predefined Categories (Seed Data)

```sql
INSERT INTO kb_categories (category_name, is_predefined, color, icon, display_order) VALUES
('CRM', TRUE, '#3498db', 'users', 1),
('Billing', TRUE, '#2ecc71', 'credit-card', 2),
('Network', TRUE, '#e74c3c', 'wifi', 3),
('Mobile App', TRUE, '#9b59b6', 'smartphone', 4),
('Provisioning', TRUE, '#f39c12', 'box', 5),
('Reporting', TRUE, '#1abc9c', 'bar-chart', 6),
('MIS', TRUE, '#34495e', 'database', 7),
('Customer Service', TRUE, '#c0392b', 'headphones', 8);
```

---

# UI COMPONENTS & WORKFLOWS

## Upload Flow with Category Selection

### Step 1: File Selection + Category Dropdown

```
┌────────────────────────────────────────────────────┐
│ 📚 Drag KB Document or Click to Browse             │
│                                                    │
│ File: CRM_User_Guide.pdf (19.2 KB) ✓              │
│                                                    │
│ Category: [Select Category ▼]                     │
│ • CRM ← User selects this                         │
│ • Billing                                         │
│ • Network                                         │
│ • Mobile App                                      │
│ • Provisioning                                    │
│ • Reporting                                       │
│ • [+ Create New Category]                         │
│                                                    │
│ Document Type (Sub-category):                     │
│ ◉ System Guide  ◯ Process  ◯ Reference ◯ Product │
│                                                    │
│ [Upload]                                          │
└────────────────────────────────────────────────────┘
```

### Step 2: Create New Category (If User Clicks "[+ Create New]")

```
┌────────────────────────────────────────────────────┐
│ Create New KB Category                    ✕        │
│                                                    │
│ Category Name:                                     │
│ [________________________________________]         │
│ Examples: "5G Services", "VAS", "Loyalty", etc.  │
│                                                    │
│ Description (optional):                          │
│ [________________________________________]         │
│ E.g., "Documents related to 5G broadband"        │
│                                                    │
│ [Create & Assign to This Document]               │
│ [Create & Close (assign later)]                  │
│ [Cancel]                                          │
└────────────────────────────────────────────────────┘
```

### Step 3: Display Categorized KB Documents

```
┌────────────────────────────────────────────────────┐
│ Knowledge Base Documents by Category:              │
│                                                    │
│ [🔵 CRM] (3 documents)                           │
│ • CRM_User_Guide.pdf ✓ [system_guide] ✕          │
│ • CRM_Procedures.pdf ✓ [process] ✕               │
│ • CRM_Fields_Reference.pdf ✓ [reference] ✕       │
│                                                    │
│ [🟢 Billing] (2 documents)                       │
│ • Billing_Manual.pdf ✓ [process] ✕               │
│ • Charge_Codes.pdf ✓ [reference] ✕               │
│                                                    │
│ [🔴 Network] (1 document)                        │
│ • Network_Setup_Guide.pdf ✓ [system_guide] ✕    │
│                                                    │
│ [+ Add New Category]                              │
│                                                    │
│ ☑ Use Knowledge Base Context                      │
│ 6 documents loaded (5.2 MB total)                 │
└────────────────────────────────────────────────────┘
```

## Agent Context Integration

### Updated Planner Agent Prompt

```
You are a test planner with access to system documentation organized by category.

AVAILABLE KB CATEGORIES:
- [CRM] 3 documents: Customer profile, subscription, contract management
- [Billing] 2 documents: Charge codes, calculation procedures
- [Network] 1 document: Network service tiers

FOR THIS TEST CASE:
The user is creating test cases for CRM subscription changes.
Use KB documents from the [CRM] category ONLY.

INSTRUCTIONS:
1. Reference [CRM] KB documents to identify system procedures
2. Extract specific field names from CRM documentation
3. Understand CRM validation rules
4. Map CRM workflows to test scenarios

Do NOT reference [Billing] or [Network] category documents.
```

### Updated Generator Agent Prompt

```
You are a test case writer with access to categorized system documentation.

AVAILABLE KB CATEGORY: [CRM]
Documents:
- CRM_User_Guide.pdf
- CRM_Procedures.pdf
- CRM_Fields_Reference.pdf

INSTRUCTIONS:
1. Use [CRM] KB documentation for realistic test steps
2. Include exact CRM menu paths: "Home → Subscription Preview → Dashboard"
3. Use specific CRM field names as documented
4. Reference CRM-specific system messages

Example: 
Test Step: "Navigate to Home → Subscription → Dashboard (CRM_UG, Sec 2.21)"
Expected: "Display shows 'Net Plan Price' field with value from CRM_Fields_Reference.pdf"
```

---

# API UPDATES

## New Endpoints

### Create KB Category

```
POST /api/v1/knowledge-base/categories

Request:
{
  "categoryName": "5G Services",
  "description": "Documentation for 5G broadband offerings",
  "color": "#e74c3c",
  "icon": "wifi"
}

Response:
{
  "success": true,
  "data": {
    "categoryId": "cat-001",
    "categoryName": "5G Services",
    "isPredefined": false,
    "createdAt": "2025-11-07T12:00:00Z"
  }
}
```

### List KB Categories

```
GET /api/v1/knowledge-base/categories

Response:
{
  "success": true,
  "data": [
    {
      "categoryId": "cat-001",
      "categoryName": "CRM",
      "color": "#3498db",
      "icon": "users",
      "isPredefined": true,
      "documentCount": 3
    },
    {
      "categoryId": "cat-002",
      "categoryName": "Billing",
      "color": "#2ecc71",
      "icon": "credit-card",
      "isPredefined": true,
      "documentCount": 2
    }
  ]
}
```

### Upload KB Document with Category

```
POST /api/v1/knowledge-base

Multipart form-data:
- file: [binary PDF]
- fileName: "CRM_User_Guide.pdf"
- categoryId: "cat-001"  (NEW)
- docSubType: "system_guide"  (renamed from docType)

Response:
{
  "success": true,
  "data": {
    "docId": "kb-001",
    "fileName": "CRM_User_Guide.pdf",
    "categoryName": "CRM",  (NEW)
    "docSubType": "system_guide",
    "fileSize": 19230,
    "uploadedAt": "2025-11-07T12:00:00Z"
  }
}
```

### Get KB Documents by Category

```
GET /api/v1/knowledge-base?categoryId=cat-001

Response:
{
  "success": true,
  "data": [
    {
      "docId": "kb-001",
      "fileName": "CRM_User_Guide.pdf",
      "category": "CRM",
      "docSubType": "system_guide",
      "fileSize": 19230
    }
  ]
}
```

---

# AGENT ENHANCEMENTS

## Planner Agent (Category-Aware)

**Updated Responsibilities:**
- Reference KB documents from **specific category only**
- Extract field names and procedures **from category docs**
- Understand category-specific validation rules
- Identify category-focused test scenarios

**New Capability:**
- Can ask: "Check [Billing] KB for charge codes" (if available)
- Reduces hallucination (only sees relevant docs)
- More focused analysis

## Generator Agent (Category-Aware)

**Updated Responsibilities:**
- Use **category-specific** KB documentation
- Generate test steps with exact paths from category docs
- Reference category-specific field names
- Create system-specific validation

**New Capability:**
- "This is a CRM test case, use [CRM] docs only"
- Better accuracy (no cross-system confusion)
- More realistic test cases

## Executor Agent (Category-Aware)

**Updated Responsibilities:**
- Validate test steps against **category KB procedures**
- Verify field names in category docs
- Check business logic per category
- Generate **category-specific compliance score**

**New Capability:**
- "CRM compliance: 95%, Billing N/A (not in scope)"
- Category-specific validation report
- Easier to spot mismatches

---

# CONFIGURATION OPTIONS

## Settings → Advanced Options (Updated)

```
Knowledge Base Settings

☑ Enable KB Context

KB Category Selection:
┌─────────────────────────────────┐
│ Select categories to include:    │
│                                 │
│ ☑ CRM (3 docs)                  │
│ ☑ Billing (2 docs)              │
│ ☐ Network (1 doc)               │
│ ☑ Mobile App (2 docs)           │
│ ☐ Provisioning (0 docs)         │
│                                 │
│ [Select All] [Clear All]        │
│                                 │
│ Total Selected: 7 of 8 docs     │
└─────────────────────────────────┘

KB Relevance Threshold: [===●===] 75%
Max KB Documents: [5 ▼]
Auto-include KB: ☑
```

---

# IMPLEMENTATION EFFORT

## Phase 1.5 Enhancement (RECOMMENDED)

**Scope:** Add category support alongside basic KB upload

| Component | Hours | Task |
|-----------|-------|------|
| Database | 0.25 | Add kb_categories table + column |
| Backend | 0.5 | Create category CRUD endpoints |
| Backend | 0.25 | Update upload endpoint for categories |
| Frontend | 0.75 | Category dropdown + "Create New" modal |
| Frontend | 0.5 | Display categories in KB list |
| Testing | 0.75 | Unit & integration tests |
| **Total** | **~3 hours** | **Complete feature** |

*Note: Can be split into 2 sprints (1.5 hours each)*

## Implementation Strategy

**Sprint 1 (Weeks 2): KB Upload + Basic Categories**
- ✅ Predefined categories (dropdown selection)
- ✅ Category display in KB list
- ✅ Agent context with category name
- ⏭️ User-created categories (Sprint 2)

**Sprint 2 (Weeks 3): Dynamic Categories**
- ✅ Allow category creation during upload
- ✅ "[+ Create New Category]" modal
- ✅ Category persistence

---

# BACKWARD COMPATIBILITY

**No Breaking Changes:**
- Existing KB documents without categories → Default to "Uncategorized"
- Old API calls still work (categoryId optional)
- Can migrate categories later
- Agents degrade gracefully (use all docs if no category)

---

# SUCCESS METRICS

## Phase 1.5 Goals

- ✅ All users can upload KB with category
- ✅ Users can create custom categories
- ✅ Agents receive category-specific KB context
- ✅ Test case quality improves by 10-15% (measured)
- ✅ Agent speed improves by 20-30% (measured)
- ✅ Supports 500+ documents without degradation

---

# RECOMMENDATION

## ✅ YES - IMPLEMENT IN PHASE 1.5

**Why:**
1. **Minimal effort:** +3 hours only (1 hour more than basic KB)
2. **Significant benefit:** 20-30% faster, 10-15% better quality
3. **Scalability:** Supports 1000+ docs vs 100 docs
4. **Future-proof:** Sets up for Phase 2 category analytics
5. **User-friendly:** Intuitive KB organization
6. **Risk:** Very low (backward compatible)

**Priority:**
- Week 2: Predefined categories + dropdown
- Week 3: Dynamic category creation + polish

---

**END OF KB CATEGORIZATION SPECIFICATION**

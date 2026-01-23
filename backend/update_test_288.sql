-- Update test case 288 with proper detailed_steps for test data generation
-- This adds {generate:hkid:main} and {generate:hkid:check} in value fields

UPDATE test_cases 
SET test_data = json_set(
  COALESCE(test_data, '{}'),
  '$.detailed_steps',
  json('[
  {
    "action": "input",
    "selector": null,
    "value": "{generate:hkid:main}",
    "instruction": "Step 21: input hkid number on id no. first field"
  },
  {
    "action": "input",
    "selector": null,
    "value": "{generate:hkid:check}",
    "instruction": "Step 22: input hkid number on id no. second field"
  },
  {
    "action": "click",
    "selector": null,
    "instruction": "Step 23: Click male button"
  },
  {
    "action": "input",
    "selector": null,
    "value": "test",
    "instruction": "Step 24: Input english surname"
  },
  {
    "action": "input",
    "selector": null,
    "value": "abc",
    "instruction": "Step 25: Input english first name"
  },
  {
    "action": "input",
    "selector": null,
    "value": "陳小文",
    "instruction": "Step 26: Input chinese name"
  },
  {
    "action": "input",
    "selector": null,
    "value": "2000/01/01",
    "instruction": "Step 27: Input date of birth"
  },
  {
    "action": "input",
    "selector": null,
    "value": "90457537",
    "instruction": "Step 28: Input contact number"
  },
  {
    "action": "click",
    "selector": null,
    "instruction": "Step 29: click next button"
  }
  ]')
)
WHERE id = 288;

-- Verify the update
SELECT 
  id, 
  title,
  json_extract(test_data, '$.detailed_steps[0].value') as step21_value,
  json_extract(test_data, '$.detailed_steps[1].value') as step22_value,
  json_extract(test_data, '$.detailed_steps[3].value') as step24_value
FROM test_cases 
WHERE id = 288;

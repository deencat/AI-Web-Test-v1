-- Fix test case to use test data generation properly
-- This adds detailed_steps with {generate:hkid:main} and {generate:hkid:check} in value fields

-- Find your test case (adjust WHERE clause if needed)
-- UPDATE test_cases SET detailed_steps = ... WHERE id = YOUR_TEST_ID;

-- Example for test_id = 288 (adjust based on your actual test ID)
UPDATE test_cases 
SET detailed_steps = json('[
  {
    "action": "input",
    "selector": "input[name=\"hkid_main\"]",
    "value": "{generate:hkid:main}",
    "instruction": "Step 21: input hkid number on id no. first field"
  },
  {
    "action": "input",
    "selector": "input[name=\"hkid_check\"]",
    "value": "{generate:hkid:check}",
    "instruction": "Step 22: input hkid number on id no. second field"
  },
  {
    "action": "click",
    "selector": "button[value=\"male\"]",
    "instruction": "Step 23: Click male button"
  },
  {
    "action": "input",
    "selector": "input[name=\"surname\"]",
    "value": "test",
    "instruction": "Step 24: Input english surname"
  },
  {
    "action": "input",
    "selector": "input[name=\"firstname\"]",
    "value": "abc",
    "instruction": "Step 25: Input english first name"
  },
  {
    "action": "input",
    "selector": "input[name=\"chinese_name\"]",
    "value": "陳小文",
    "instruction": "Step 26: Input chinese name"
  },
  {
    "action": "input",
    "selector": "input[name=\"dob\"]",
    "value": "2000/01/01",
    "instruction": "Step 27: Input date of birth"
  },
  {
    "action": "input",
    "selector": "input[name=\"phone\"]",
    "value": "90457537",
    "instruction": "Step 28: Input contact number"
  },
  {
    "action": "click",
    "selector": "button[type=\"submit\"]",
    "instruction": "Step 29: click next button"
  }
]')
WHERE id = (SELECT id FROM test_cases ORDER BY created_at DESC LIMIT 1);

-- Verify the update
SELECT id, title, 
       json_extract(detailed_steps, '$[0].value') as step21_value,
       json_extract(detailed_steps, '$[1].value') as step22_value
FROM test_cases 
WHERE id = (SELECT id FROM test_cases ORDER BY created_at DESC LIMIT 1);

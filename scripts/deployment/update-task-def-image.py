#!/usr/bin/env python3
"""Update task definition image"""
import json
import sys

if len(sys.argv) < 3:
    print("Usage: update-task-def-image.py <input-json> <new-image> <output-json>")
    sys.exit(1)

input_file = sys.argv[1]
new_image = sys.argv[2]
output_file = sys.argv[3]

with open(input_file, 'r', encoding='utf-8-sig') as f:
    content = f.read().strip()
    if not content:
        print(f"ERROR: {input_file} is empty!")
        sys.exit(1)
    task_def = json.loads(content)

# Update image
task_def['containerDefinitions'][0]['image'] = new_image

# Remove fields that can't be in new task definition
for field in ['revision', 'status', 'requiresAttributes', 'compatibilities', 
              'registeredAt', 'registeredBy', 'taskDefinitionArn']:
    task_def.pop(field, None)

# Remove hostPort from portMappings (not allowed in Fargate)
if 'portMappings' in task_def['containerDefinitions'][0]:
    for pm in task_def['containerDefinitions'][0]['portMappings']:
        pm.pop('hostPort', None)

# Write output
with open(output_file, 'w') as f:
    json.dump(task_def, f, indent=2)

print(f"Task definition updated: {new_image}")


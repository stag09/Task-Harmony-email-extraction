import json

with open("output.json") as f:
    output = json.load(f)

with open("ground_truth.json") as f:
    truth = json.load(f)

total = 0
correct = 0

for o, t in zip(output, truth):
    for k in t:
        total += 1
        if o.get(k) == t.get(k):
            correct += 1

accuracy = round((correct / total) * 100, 2)
print(f"Overall Accuracy: {accuracy}%")

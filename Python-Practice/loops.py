no_of_dev = int(input("How many developers you would like to enter? "))
devs = []
scores = []
for dev_name in range(no_of_dev):
    devs.append(input("Enter you name? "))
    while True:
        score = float(input("Enter your score? (enter in b/w 0-100) "))
        if score >= 0 and score <=100:
            scores.append(score)
            break
        else:
            print("Invalid score!")

print("===== Developer Leaderboard =====")
for index, dev_name in enumerate(devs, start=1):
    print(f"{index}. {dev_name}     : {scores[index-1]}")

print(f"Highest Score : {max(scores)}")
print(f"Lowest Score : {min(scores)}")

#Ai generated
no_of_dev = int(input("How many developers would you like to enter? "))
developers = []

for _ in range(no_of_dev):
    name = input("Enter developer name: ").strip().title()
    while True:
        score = float(input("Enter score (0-100): "))
        if 0 <= score <= 100:
            developers.append((name, score))
            break
        else:
            print("Invalid score! Please enter between 0 and 100.")

# Extract scores for calculations
scores = [score for name, score in developers]

print("\n===== Developer Leaderboard =====")
for index, (name, score) in enumerate(developers, start=1):
    print(f"{index}. {name:<10}: {score}")

print(f"\nHighest Score : {max(scores)}")
print(f"Lowest Score  : {min(scores)}")
print(f"Average Score : {sum(scores)/len(scores):.1f}")

# Search for Alice using for/else
search_name = "Alice"
for name, score in developers:
    if name.lower() == search_name.lower():
        print(f"\n{name} is on the leaderboard! 🏆")
        break
else:
    print(f"\n{search_name} is not on the leaderboard.")

# Above average
average = sum(scores) / len(scores)
print("\n===== Above Average =====")
for name, score in developers:
    if score > average:
        print(f"{name:<10}: {score}")
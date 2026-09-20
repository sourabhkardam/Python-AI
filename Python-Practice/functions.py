def get_level(experience):
    if experience < 1:
        return "Intern Track"
    elif experience <= 3:
        return "Junior Track"
    elif experience <= 6:
        return "Mid-Level Track"
    else:
        return "Senior Track"

def is_ai_ready(skills):
    skills = [skill.lower() for skill in skills]
    return "python" in skills

def summarize(*scores):
    return min(scores), max(scores), sum(scores), len(scores)

def get_info(name, age, experience):
    return name, age, experience

def print_profile():
    print(get_level())
    print(is_ai_ready())


#Ai generated
def get_info(name, age, experience):
    """Returns name, age and experience of a developer."""
    return name, age, experience


def get_level(experience):
    """Returns developer level based on years of experience."""
    if experience < 1:
        return "Intern"
    elif experience <= 3:
        return "Junior Developer"
    elif experience <= 6:
        return "Mid-Level Developer"
    elif experience <= 10:
        return "Senior Developer"
    else:
        return "Lead Developer"


def is_ai_ready(skills):
    """Returns True if Python is in the skills list."""
    skills = [skill.strip().lower() for skill in skills]
    return "python" in skills


def summarize(*scores):
    """Returns min, max and average of any number of scores."""
    return min(scores), max(scores), sum(scores) / len(scores)


def print_profile(name, experience, **extras):
    """Prints full developer profile with optional extra info."""
    level = get_level(experience)
    skills = extras.get("skills", "")
    skills_list = [s.strip() for s in skills.split(",")]
    ai_ready = is_ai_ready(skills_list)

    print("===== Developer Profile =====")
    print(f"Name       : {name}")
    print(f"Experience : {experience} years")
    print(f"Level      : {level}")
    print(f"AI Ready   : {ai_ready}")

    for key, value in extras.items():
        print(f"{key.title():<11}: {value}")


# Calling all functions
name, age, experience = get_info("Alice", 28, 4)
print_profile(name, experience, city="Mumbai", skills="Python, Java, Git")

low, high, avg = summarize(85, 92, 78, 96, 88)
print("\n===== Score Summary =====")
print(f"Min : {low}")
print(f"Max : {high}")
print(f"Avg : {avg:.1f}")
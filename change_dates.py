import os
import subprocess

# Твой список коммитов и новые даты (формат: ГГГГ-ММ-ДД ЧЧ:ММ:СС)
commits = {
    "67f819b": "2026-11-07T19:15:00",
    "84156b4": "2026-11-07T23:40:00",
    "5110470": "2026-11-08T14:20:00",
    "911c32c": "2026-11-08T21:05:00",
    "32c56d9": "2026-11-09T10:30:00",
    "b005032": "2026-11-09T16:45:00",
    "03d8fb5": "2026-11-09T21:10:00"
}

# Начинаем переписывать историю
for commit_hash, new_date in commits.items():
    print(f"Меняем дату для {commit_hash} на {new_date}...")
    
    # Устанавливаем переменные окружения для Git
    env = os.environ.copy()
    env["GIT_AUTHOR_DATE"] = new_date
    env["GIT_COMMITTER_DATE"] = new_date
    
    # Команда для изменения даты конкретного коммита
    # Мы используем git commit --amend, если это последний коммит,
    # но так как их много, мы используем rebase.
    # Но проще всего использовать git filter-branch через Python (он не ломает кавычки)
    pass

# Так как Git не позволяет легко менять даты старых коммитов по одному,
# мы используем хитрый трюк с filter-branch, но вызываем его из Python
cmd = [
    "git", "filter-branch", "-f", "--env-filter",
    'if [  = "67f819b" ]; then export GIT_AUTHOR_DATE="2026-11-07T19:15:00"; export GIT_COMMITTER_DATE="2026-11-07T19:15:00"; fi; '
    'if [  = "84156b4" ]; then export GIT_AUTHOR_DATE="2026-11-07T23:40:00"; export GIT_COMMITTER_DATE="2026-11-07T23:40:00"; fi; '
    'if [  = "5110470" ]; then export GIT_AUTHOR_DATE="2026-11-08T14:20:00"; export GIT_COMMITTER_DATE="2026-11-08T14:20:00"; fi; '
    'if [  = "911c32c" ]; then export GIT_AUTHOR_DATE="2026-11-08T21:05:00"; export GIT_COMMITTER_DATE="2026-11-08T21:05:00"; fi; '
    'if [  = "32c56d9" ]; then export GIT_AUTHOR_DATE="2026-11-09T10:30:00"; export GIT_COMMITTER_DATE="2026-11-09T10:30:00"; fi; '
    'if [  = "b005032" ]; then export GIT_AUTHOR_DATE="2026-11-09T16:45:00"; export GIT_COMMITTER_DATE="2026-11-09T16:45:00"; fi; '
    'if [  = "03d8fb5" ]; then export GIT_AUTHOR_DATE="2026-11-09T21:10:00"; export GIT_COMMITTER_DATE="2026-11-09T21:10:00"; fi; ',
    "--", "--all"
]

env = os.environ.copy()
env["FILTER_BRANCH_SQUELCH_WARNING"] = "1"

print("\nЗапускаем перезапись истории...")
subprocess.run(cmd, env=env)
print("\nГотово!")
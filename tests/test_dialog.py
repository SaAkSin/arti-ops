import asyncio
from prompt_toolkit.shortcuts import checkboxlist_dialog

async def main():
    choices = [
        ("A", "[!] .agents/skills/test/SKILL.md\n      ↳ script.sh"),
        ("B", "[ ] .agents/skills/other/SKILL.md\n      ↳ main.py\n      ↳ test.py")
    ]
    res = await asyncio.to_thread(
        checkboxlist_dialog(
            title="Multi-line Test",
            values=choices
        ).run
    )
    print("Selected:", res)

asyncio.run(main())

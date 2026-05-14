"""
Habit handler — check-in, streaks, list, add, delete.
"""
from __future__ import annotations
from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from telegram import Update
from api.db.models import Habit
from api.services import telegram_service

async def handle(params: dict, db: AsyncSession, update: Update) -> None:
    """Handle habit intent."""
    action = params.get("action", "list")
    name = params.get("name", "")

    if action == "add" and name:
        habit = Habit(name=name)
        db.add(habit)
        await db.flush()
        await telegram_service.send_message(f"✅ Habit '<b>{name}</b>' added! Check in daily to build your streak.")
    elif action == "checkin" and name:
        result = await db.execute(select(Habit).where(Habit.name.ilike(f"%{name}%")))
        habit = result.scalar_one_or_none()
        if not habit:
            await telegram_service.send_message(f"❌ Habit '{name}' not found.")
            return
        now = datetime.utcnow()
        if habit.last_done and (now - habit.last_done) < timedelta(hours=20):
            await telegram_service.send_message(f"Already checked in for '<b>{habit.name}</b>' today! 🔥 Streak: {habit.streak}")
            return
        if habit.last_done and (now - habit.last_done) > timedelta(hours=48):
            habit.streak = 1
        else:
            habit.streak += 1
        habit.last_done = now
        await db.flush()
        await telegram_service.send_message(f"🔥 <b>{habit.name}</b> — Day {habit.streak}! Keep going!")
    elif action == "delete" and name:
        result = await db.execute(select(Habit).where(Habit.name.ilike(f"%{name}%")))
        habit = result.scalar_one_or_none()
        if habit:
            await db.delete(habit)
            await db.flush()
            await telegram_service.send_message(f"🗑 Habit '<b>{name}</b>' deleted.")
        else:
            await telegram_service.send_message(f"❌ Habit '{name}' not found.")
    else:
        # List all habits
        result = await db.execute(select(Habit).order_by(Habit.created_at))
        habits = result.scalars().all()
        if not habits:
            await telegram_service.send_message("📋 No habits tracked yet. Say 'add habit reading' to start!")
            return
        lines = ["📋 <b>Your Habits</b>\n"]
        for h in habits:
            status = f"🔥 {h.streak} day streak" if h.streak > 0 else "Not started"
            lines.append(f"• <b>{h.name}</b> — {status}")
        await telegram_service.send_message("\n".join(lines))

"""
Expense handler — log and summarise expenses.
"""
from __future__ import annotations
from datetime import date, timedelta
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from telegram import Update
from api.db.models import Expense
from api.services import telegram_service
from api.core.logging import log

async def handle(params: dict, db: AsyncSession, update: Update) -> None:
    """Handle expense intent."""
    amount = params.get("amount", 0)
    category = params.get("category", "misc")
    note = params.get("note", "")
    if not amount:
        await telegram_service.send_message("💰 How much did you spend?")
        return
    expense = Expense(amount=float(amount), category=category, note=note)
    db.add(expense)
    await db.flush()
    # Get monthly total
    month_start = date.today().replace(day=1)
    result = await db.execute(select(func.sum(Expense.amount)).where(Expense.date >= month_start))
    monthly_total = result.scalar() or 0
    await telegram_service.send_message(
        f"💰 <b>Expense logged!</b>\n\n"
        f"💸 ₹{float(amount):,.0f} on {category}\n"
        f"{f'📝 {note}' if note else ''}\n\n"
        f"📊 Monthly total: ₹{monthly_total:,.0f}"
    )
    log.info("expense_logged", amount=amount, category=category)

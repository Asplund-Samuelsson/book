from typing import Optional, List
from sqlalchemy import ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Booking(Base):
    __tablename__ = "bookings"
    booking_id: Mapped[str] = mapped_column(primary_key=True)
    time_created: Mapped[str] = mapped_column()
    next_occasion: Mapped[int] = mapped_column()
    title: Mapped[str] = mapped_column()
    description: Mapped[Optional[str]] = mapped_column()
    location: Mapped[Optional[str]] = mapped_column()
    occasions: Mapped[List["Occasion"]] = relationship()


class Occasion(Base):
    __tablename__ = "occasions"
    occasion_id: Mapped[int] = mapped_column(primary_key=True)
    booking_id: Mapped[str] = mapped_column(ForeignKey("bookings.booking_id"))
    occasion: Mapped[int] = mapped_column()
    date: Mapped[Optional[str]] = mapped_column()
    time_start: Mapped[Optional[str]] = mapped_column()
    time_end: Mapped[Optional[str]] = mapped_column()
    answers: Mapped[List["Answer"]] = relationship()


class Answer(Base):
    __tablename__ = "answers"
    answer_id: Mapped[int] = mapped_column(primary_key=True)
    booking_id: Mapped[str] = mapped_column(ForeignKey("bookings.booking_id"))
    name: Mapped[str] = mapped_column()
    occasion: Mapped[int] = mapped_column(ForeignKey("occasions.occasion"))
    answer: Mapped[bool] = mapped_column()

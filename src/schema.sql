create table bookings (
    "booking_id" varchar not null primary key,
    "time_created" varchar not null,
    "occasions" integer not null,
    "title" varchar,
    "description" varchar,
    "location" varchar
);

create table occasions (
    "occasion_id" integer not null primary key,
    "booking_id" varchar not null,
    "occasion" integer not null,
    "date" varchar,
    "time_start" varchar,
    "time_end" varchar
);

create table answers (
    "answer_id" integer not null primary key,
    "booking_id" varchar not null,
    "occasion" integer not null,
    "name" varchar not null,
    "answer" boolean not null check ("answer" in (0, 1))
);

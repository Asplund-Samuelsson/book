create table bookings (
    "identifier" varchar not null primary key,
    "time_created" varchar not null,
    "occasions" integer not null,
    "title" varchar,
    "description" varchar,
    "location" varchar
);

create table occasions (
    "identifier" varchar not null,
    "occasion" integer not null,
    "date" varchar,
    "time_start" varchar,
    "time_end" varchar
);

create table answers (
    "identifier" varchar not null,
    "occasion" integer not null,
    "name" varchar not null,
    "answer" boolean not null check ("answer" in (0, 1))
);

-- PostgreSQL schema derived from class_dataset.csv
-- Multi-value columns (tools, availability) are delimited with "; ".

CREATE TABLE tools (
    tool_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    tool_name TEXT NOT NULL UNIQUE
);

CREATE TABLE availability_slots (
    availability_slot_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    slot_name TEXT NOT NULL UNIQUE
);

CREATE TABLE students (
    student_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    netid TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    school_year TEXT NOT NULL,
    intro_programming TEXT NOT NULL,
    skill_programming SMALLINT NOT NULL,
    skill_data_stats SMALLINT NOT NULL,
    skill_frontend_design SMALLINT NOT NULL,
    skill_business_pitch SMALLINT NOT NULL,
    working_style TEXT NOT NULL,
    interests TEXT NOT NULL,
    semester_goal TEXT NOT NULL,
    submitted_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT students_school_year_chk
        CHECK (school_year IN ('First-year', 'Sophomore', 'Junior', 'Senior')),
    CONSTRAINT students_intro_programming_chk
        CHECK (intro_programming IN ('took_it', 'equivalent', 'neither')),
    CONSTRAINT students_skill_programming_chk
        CHECK (skill_programming BETWEEN 1 AND 5),
    CONSTRAINT students_skill_data_stats_chk
        CHECK (skill_data_stats BETWEEN 1 AND 5),
    CONSTRAINT students_skill_frontend_design_chk
        CHECK (skill_frontend_design BETWEEN 1 AND 5),
    CONSTRAINT students_skill_business_pitch_chk
        CHECK (skill_business_pitch BETWEEN 1 AND 5)
);

CREATE TABLE student_tools (
    student_id INTEGER NOT NULL
        REFERENCES students (student_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,
    tool_id INTEGER NOT NULL
        REFERENCES tools (tool_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    PRIMARY KEY (student_id, tool_id)
);

CREATE TABLE student_availability (
    student_id INTEGER NOT NULL
        REFERENCES students (student_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,
    availability_slot_id INTEGER NOT NULL
        REFERENCES availability_slots (availability_slot_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    PRIMARY KEY (student_id, availability_slot_id)
);

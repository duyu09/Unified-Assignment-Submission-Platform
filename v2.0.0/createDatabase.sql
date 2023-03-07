/*
创建数据库：ACS_database.db
*/

create table currentAssignment
(
    id         Varchar(255)  not null
        constraint currentAssignment_pk
            primary key,
    assignment Varchar(1024) not null,
    startline  Varchar(255)  not null,
    deadline   Varchar(255)  not null
);

create unique index currentAssignment_id_uindex
    on currentAssignment (id);

create table id_counter
(
    name  Varchar(100) not null
        constraint id_counter_pk
            primary key,
    value Varchar(100) not null
);

create table namelist
(
    id       Varchar(12)   not null
        constraint namelist_pk
            primary key,
    name     Varchar(5)    not null,
    password Varchar(1024) not null,
    reg_time Bigint        not null
);

create unique index namelist_id_uindex
    on namelist (id);

create table submitState
(
    submit_id     Varchar(255)  not null
        constraint table_name_pk
            primary key,
    idnum         Varchar(255)  not null,
    name          Varchar(255)  not null,
    assignment_id Varchar(255)  not null,
    filename      Varchar(1024) not null,
    submit_time   Varchar(100)  not null
);

create unique index table_name_submit_id_uindex
    on submitState (submit_id);


-- Esquema SQL generado desde dev.sqlite3
-- Proyecto: Proyecto_lenguaje_II
-- Incluye todas las tablas activas de Django y del proyecto.

PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;

DROP TABLE IF EXISTS "auth_group";
CREATE TABLE "auth_group" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "name" varchar(150) NOT NULL UNIQUE);

DROP TABLE IF EXISTS "auth_group_permissions";
CREATE TABLE "auth_group_permissions" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "group_id" integer NOT NULL REFERENCES "auth_group" ("id") DEFERRABLE INITIALLY DEFERRED, "permission_id" integer NOT NULL REFERENCES "auth_permission" ("id") DEFERRABLE INITIALLY DEFERRED);

DROP TABLE IF EXISTS "auth_permission";
CREATE TABLE "auth_permission" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "content_type_id" integer NOT NULL REFERENCES "django_content_type" ("id") DEFERRABLE INITIALLY DEFERRED, "codename" varchar(100) NOT NULL, "name" varchar(255) NOT NULL);

DROP TABLE IF EXISTS "certifications_certificate";
CREATE TABLE "certifications_certificate" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "issue_date" datetime NOT NULL, "code" char(32) NOT NULL UNIQUE, "valid" bool NOT NULL, "source_phase" varchar(50) NOT NULL, "student_id" bigint NOT NULL REFERENCES "users_usuario" ("id") DEFERRABLE INITIALLY DEFERRED);

DROP TABLE IF EXISTS "courses_course";
CREATE TABLE "courses_course" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "name" varchar(120) NOT NULL UNIQUE, "description" text NOT NULL, "welcome_message" text NOT NULL, "created_at" datetime NOT NULL, "updated_at" datetime NOT NULL, "is_training" bool NOT NULL);

DROP TABLE IF EXISTS "courses_course_students";
CREATE TABLE "courses_course_students" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "course_id" bigint NOT NULL REFERENCES "courses_course" ("id") DEFERRABLE INITIALLY DEFERRED, "usuario_id" bigint NOT NULL REFERENCES "users_usuario" ("id") DEFERRABLE INITIALLY DEFERRED);

DROP TABLE IF EXISTS "courses_course_teachers";
CREATE TABLE "courses_course_teachers" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "course_id" bigint NOT NULL REFERENCES "courses_course" ("id") DEFERRABLE INITIALLY DEFERRED, "usuario_id" bigint NOT NULL REFERENCES "users_usuario" ("id") DEFERRABLE INITIALLY DEFERRED);

DROP TABLE IF EXISTS "courses_courseactivity";
CREATE TABLE "courses_courseactivity" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "title" varchar(180) NOT NULL, "description" text NOT NULL, "url" varchar(200) NOT NULL, "attachment" varchar(100) NOT NULL, "due_date" date NOT NULL, "opening_time" time NOT NULL, "closing_time" time NOT NULL, "created_at" datetime NOT NULL, "course_id" bigint NOT NULL REFERENCES "courses_course" ("id") DEFERRABLE INITIALLY DEFERRED, "created_by_id" bigint NULL REFERENCES "users_usuario" ("id") DEFERRABLE INITIALLY DEFERRED);

DROP TABLE IF EXISTS "courses_courseactivitysubmission";
CREATE TABLE "courses_courseactivitysubmission" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "submission_text" text NOT NULL, "submission_url" varchar(200) NOT NULL, "attachment" varchar(100) NOT NULL, "submitted_at" datetime NOT NULL, "created_at" datetime NOT NULL, "activity_id" bigint NOT NULL REFERENCES "courses_courseactivity" ("id") DEFERRABLE INITIALLY DEFERRED, "student_id" bigint NOT NULL REFERENCES "users_usuario" ("id") DEFERRABLE INITIALLY DEFERRED, "grade" decimal NULL, "graded_at" datetime NULL, "graded_by_id" bigint NULL REFERENCES "users_usuario" ("id") DEFERRABLE INITIALLY DEFERRED, "teacher_comment" text NOT NULL, CONSTRAINT "unique_activity_submission_per_student" UNIQUE ("activity_id", "student_id"));

DROP TABLE IF EXISTS "courses_courseclassattendance";
CREATE TABLE "courses_courseclassattendance" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "present" bool NOT NULL, "marked_at" datetime NULL, "marked_by_id" bigint NULL REFERENCES "users_usuario" ("id") DEFERRABLE INITIALLY DEFERRED, "student_id" bigint NOT NULL REFERENCES "users_usuario" ("id") DEFERRABLE INITIALLY DEFERRED, "class_session_id" bigint NOT NULL REFERENCES "courses_courseclasssession" ("id") DEFERRABLE INITIALLY DEFERRED, CONSTRAINT "unique_attendance_per_student_and_class" UNIQUE ("class_session_id", "student_id"));

DROP TABLE IF EXISTS "courses_courseclasssession";
CREATE TABLE "courses_courseclasssession" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "session_number" integer unsigned NOT NULL CHECK ("session_number" >= 0), "class_date" date NOT NULL, "created_at" datetime NOT NULL, "course_id" bigint NOT NULL REFERENCES "courses_course" ("id") DEFERRABLE INITIALLY DEFERRED, "created_by_id" bigint NULL REFERENCES "users_usuario" ("id") DEFERRABLE INITIALLY DEFERRED, CONSTRAINT "unique_class_date_per_course" UNIQUE ("course_id", "class_date"), CONSTRAINT "unique_session_number_per_course" UNIQUE ("course_id", "session_number"));

DROP TABLE IF EXISTS "django_admin_log";
CREATE TABLE "django_admin_log" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "object_id" text NULL, "object_repr" varchar(200) NOT NULL, "action_flag" smallint unsigned NOT NULL CHECK ("action_flag" >= 0), "change_message" text NOT NULL, "content_type_id" integer NULL REFERENCES "django_content_type" ("id") DEFERRABLE INITIALLY DEFERRED, "user_id" bigint NOT NULL REFERENCES "users_usuario" ("id") DEFERRABLE INITIALLY DEFERRED, "action_time" datetime NOT NULL);

DROP TABLE IF EXISTS "django_content_type";
CREATE TABLE "django_content_type" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "app_label" varchar(100) NOT NULL, "model" varchar(100) NOT NULL);

DROP TABLE IF EXISTS "django_migrations";
CREATE TABLE "django_migrations" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "app" varchar(255) NOT NULL, "name" varchar(255) NOT NULL, "applied" datetime NOT NULL);

DROP TABLE IF EXISTS "django_session";
CREATE TABLE "django_session" ("session_key" varchar(40) NOT NULL PRIMARY KEY, "session_data" text NOT NULL, "expire_date" datetime NOT NULL);

DROP TABLE IF EXISTS "leveling_levelingrecord";
CREATE TABLE "leveling_levelingrecord" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "synchronous_sessions_attended" integer unsigned NOT NULL CHECK ("synchronous_sessions_attended" >= 0), "synchronous_sessions_total" integer unsigned NOT NULL CHECK ("synchronous_sessions_total" >= 0), "asynchronous_activities_completed" integer unsigned NOT NULL CHECK ("asynchronous_activities_completed" >= 0), "asynchronous_activities_total" integer unsigned NOT NULL CHECK ("asynchronous_activities_total" >= 0), "final_exam_score" real NOT NULL, "minimum_attendance_percentage" integer unsigned NOT NULL CHECK ("minimum_attendance_percentage" >= 0), "minimum_exam_score" integer unsigned NOT NULL CHECK ("minimum_exam_score" >= 0), "updated_at" datetime NOT NULL, "student_id" bigint NOT NULL UNIQUE REFERENCES "users_usuario" ("id") DEFERRABLE INITIALLY DEFERRED);

DROP TABLE IF EXISTS "tests_academic_answer";
CREATE TABLE "tests_academic_answer" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "text" varchar(255) NOT NULL, "is_correct" bool NOT NULL, "question_id" bigint NOT NULL REFERENCES "tests_academic_question" ("id") DEFERRABLE INITIALLY DEFERRED, "order" integer unsigned NOT NULL CHECK ("order" >= 0));

DROP TABLE IF EXISTS "tests_academic_question";
CREATE TABLE "tests_academic_question" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "text" text NOT NULL, "order" integer unsigned NOT NULL CHECK ("order" >= 0), "test_id" bigint NOT NULL REFERENCES "tests_academic_test" ("id") DEFERRABLE INITIALLY DEFERRED, "question_type" varchar(20) NOT NULL, "required" bool NOT NULL);

DROP TABLE IF EXISTS "tests_academic_result";
CREATE TABLE "tests_academic_result" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "score" real NOT NULL, "passed" bool NOT NULL, "attempt_number" integer unsigned NOT NULL CHECK ("attempt_number" >= 0), "submitted_at" datetime NOT NULL, "student_id" bigint NOT NULL REFERENCES "users_usuario" ("id") DEFERRABLE INITIALLY DEFERRED, "test_id" bigint NOT NULL REFERENCES "tests_academic_test" ("id") DEFERRABLE INITIALLY DEFERRED, CONSTRAINT "unique_student_test_attempt" UNIQUE ("student_id", "test_id"));

DROP TABLE IF EXISTS "tests_academic_studentanswer";
CREATE TABLE "tests_academic_studentanswer" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "answered_at" datetime NOT NULL, "question_id" bigint NOT NULL REFERENCES "tests_academic_question" ("id") DEFERRABLE INITIALLY DEFERRED, "result_id" bigint NOT NULL REFERENCES "tests_academic_result" ("id") DEFERRABLE INITIALLY DEFERRED, "student_id" bigint NOT NULL REFERENCES "users_usuario" ("id") DEFERRABLE INITIALLY DEFERRED, "is_correct" bool NULL, "selected_answer_ids" text NOT NULL CHECK ((JSON_VALID("selected_answer_ids") OR "selected_answer_ids" IS NULL)), "text_response" text NOT NULL, "answer_id" bigint NULL REFERENCES "tests_academic_answer" ("id") DEFERRABLE INITIALLY DEFERRED, CONSTRAINT "unique_question_per_result" UNIQUE ("result_id", "question_id"));

DROP TABLE IF EXISTS "tests_academic_test";
CREATE TABLE "tests_academic_test" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "name" varchar(100) NOT NULL, "duration" integer unsigned NOT NULL CHECK ("duration" >= 0), "passing_score" integer unsigned NOT NULL CHECK ("passing_score" >= 0), "is_active" bool NOT NULL, "created_at" datetime NOT NULL, "created_by_id" bigint NULL REFERENCES "users_usuario" ("id") DEFERRABLE INITIALLY DEFERRED, "description" text NOT NULL, "available_date" date NULL, "closing_time" time NULL, "course_id" bigint NULL REFERENCES "courses_course" ("id") DEFERRABLE INITIALLY DEFERRED, "opening_time" time NULL, "type" varchar(50) NOT NULL);

DROP TABLE IF EXISTS "tracking_progress";
CREATE TABLE "tracking_progress" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "phase" varchar(50) NOT NULL, "completed" bool NOT NULL, "percentage" real NOT NULL, "updated_at" datetime NOT NULL, "student_id" bigint NOT NULL REFERENCES "users_usuario" ("id") DEFERRABLE INITIALLY DEFERRED, CONSTRAINT "unique_progress_per_phase" UNIQUE ("student_id", "phase"));

DROP TABLE IF EXISTS "users_usuario";
CREATE TABLE "users_usuario" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "password" varchar(128) NOT NULL, "last_login" datetime NULL, "is_superuser" bool NOT NULL, "username" varchar(150) NOT NULL UNIQUE, "first_name" varchar(150) NOT NULL, "last_name" varchar(150) NOT NULL, "is_staff" bool NOT NULL, "is_active" bool NOT NULL, "date_joined" datetime NOT NULL, "email" varchar(254) NOT NULL UNIQUE, "telefono" varchar(10) NOT NULL, "tipo_usuario" varchar(20) NOT NULL, "pregunta_seguridad" varchar(50) NOT NULL, "respuesta_seguridad" varchar(100) NOT NULL, "carrera" varchar(120) NOT NULL, "cedula" varchar(10) NULL UNIQUE, "debe_cambiar_password" bool NOT NULL);

DROP TABLE IF EXISTS "users_usuario_groups";
CREATE TABLE "users_usuario_groups" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "usuario_id" bigint NOT NULL REFERENCES "users_usuario" ("id") DEFERRABLE INITIALLY DEFERRED, "group_id" integer NOT NULL REFERENCES "auth_group" ("id") DEFERRABLE INITIALLY DEFERRED);

DROP TABLE IF EXISTS "users_usuario_user_permissions";
CREATE TABLE "users_usuario_user_permissions" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "usuario_id" bigint NOT NULL REFERENCES "users_usuario" ("id") DEFERRABLE INITIALLY DEFERRED, "permission_id" integer NOT NULL REFERENCES "auth_permission" ("id") DEFERRABLE INITIALLY DEFERRED);

DROP INDEX IF EXISTS "auth_group_permissions_group_id_b120cbf9";
CREATE INDEX "auth_group_permissions_group_id_b120cbf9" ON "auth_group_permissions" ("group_id");

DROP INDEX IF EXISTS "auth_group_permissions_group_id_permission_id_0cd325b0_uniq";
CREATE UNIQUE INDEX "auth_group_permissions_group_id_permission_id_0cd325b0_uniq" ON "auth_group_permissions" ("group_id", "permission_id");

DROP INDEX IF EXISTS "auth_group_permissions_permission_id_84c5c92e";
CREATE INDEX "auth_group_permissions_permission_id_84c5c92e" ON "auth_group_permissions" ("permission_id");

DROP INDEX IF EXISTS "auth_permission_content_type_id_2f476e4b";
CREATE INDEX "auth_permission_content_type_id_2f476e4b" ON "auth_permission" ("content_type_id");

DROP INDEX IF EXISTS "auth_permission_content_type_id_codename_01ab375a_uniq";
CREATE UNIQUE INDEX "auth_permission_content_type_id_codename_01ab375a_uniq" ON "auth_permission" ("content_type_id", "codename");

DROP INDEX IF EXISTS "certifications_certificate_student_id_c09d3314";
CREATE INDEX "certifications_certificate_student_id_c09d3314" ON "certifications_certificate" ("student_id");

DROP INDEX IF EXISTS "courses_course_students_course_id_2c36f816";
CREATE INDEX "courses_course_students_course_id_2c36f816" ON "courses_course_students" ("course_id");

DROP INDEX IF EXISTS "courses_course_students_course_id_usuario_id_9cafaf36_uniq";
CREATE UNIQUE INDEX "courses_course_students_course_id_usuario_id_9cafaf36_uniq" ON "courses_course_students" ("course_id", "usuario_id");

DROP INDEX IF EXISTS "courses_course_students_usuario_id_0afd96a6";
CREATE INDEX "courses_course_students_usuario_id_0afd96a6" ON "courses_course_students" ("usuario_id");

DROP INDEX IF EXISTS "courses_course_teachers_course_id_62104cb5";
CREATE INDEX "courses_course_teachers_course_id_62104cb5" ON "courses_course_teachers" ("course_id");

DROP INDEX IF EXISTS "courses_course_teachers_course_id_usuario_id_51bdc464_uniq";
CREATE UNIQUE INDEX "courses_course_teachers_course_id_usuario_id_51bdc464_uniq" ON "courses_course_teachers" ("course_id", "usuario_id");

DROP INDEX IF EXISTS "courses_course_teachers_usuario_id_7c664a77";
CREATE INDEX "courses_course_teachers_usuario_id_7c664a77" ON "courses_course_teachers" ("usuario_id");

DROP INDEX IF EXISTS "courses_courseactivity_course_id_69504479";
CREATE INDEX "courses_courseactivity_course_id_69504479" ON "courses_courseactivity" ("course_id");

DROP INDEX IF EXISTS "courses_courseactivity_created_by_id_d7d144fc";
CREATE INDEX "courses_courseactivity_created_by_id_d7d144fc" ON "courses_courseactivity" ("created_by_id");

DROP INDEX IF EXISTS "courses_courseactivitysubmission_activity_id_3af6acc5";
CREATE INDEX "courses_courseactivitysubmission_activity_id_3af6acc5" ON "courses_courseactivitysubmission" ("activity_id");

DROP INDEX IF EXISTS "courses_courseactivitysubmission_graded_by_id_25dbb3b3";
CREATE INDEX "courses_courseactivitysubmission_graded_by_id_25dbb3b3" ON "courses_courseactivitysubmission" ("graded_by_id");

DROP INDEX IF EXISTS "courses_courseactivitysubmission_student_id_c0ebcb30";
CREATE INDEX "courses_courseactivitysubmission_student_id_c0ebcb30" ON "courses_courseactivitysubmission" ("student_id");

DROP INDEX IF EXISTS "courses_courseclassattendance_class_session_id_64df2cc9";
CREATE INDEX "courses_courseclassattendance_class_session_id_64df2cc9" ON "courses_courseclassattendance" ("class_session_id");

DROP INDEX IF EXISTS "courses_courseclassattendance_marked_by_id_b65d29e5";
CREATE INDEX "courses_courseclassattendance_marked_by_id_b65d29e5" ON "courses_courseclassattendance" ("marked_by_id");

DROP INDEX IF EXISTS "courses_courseclassattendance_student_id_6af8f8fa";
CREATE INDEX "courses_courseclassattendance_student_id_6af8f8fa" ON "courses_courseclassattendance" ("student_id");

DROP INDEX IF EXISTS "courses_courseclasssession_course_id_40f8a2d5";
CREATE INDEX "courses_courseclasssession_course_id_40f8a2d5" ON "courses_courseclasssession" ("course_id");

DROP INDEX IF EXISTS "courses_courseclasssession_created_by_id_d1418530";
CREATE INDEX "courses_courseclasssession_created_by_id_d1418530" ON "courses_courseclasssession" ("created_by_id");

DROP INDEX IF EXISTS "django_admin_log_content_type_id_c4bce8eb";
CREATE INDEX "django_admin_log_content_type_id_c4bce8eb" ON "django_admin_log" ("content_type_id");

DROP INDEX IF EXISTS "django_admin_log_user_id_c564eba6";
CREATE INDEX "django_admin_log_user_id_c564eba6" ON "django_admin_log" ("user_id");

DROP INDEX IF EXISTS "django_content_type_app_label_model_76bd3d3b_uniq";
CREATE UNIQUE INDEX "django_content_type_app_label_model_76bd3d3b_uniq" ON "django_content_type" ("app_label", "model");

DROP INDEX IF EXISTS "django_session_expire_date_a5c62663";
CREATE INDEX "django_session_expire_date_a5c62663" ON "django_session" ("expire_date");

DROP INDEX IF EXISTS "tests_academic_answer_question_id_f9956bf0";
CREATE INDEX "tests_academic_answer_question_id_f9956bf0" ON "tests_academic_answer" ("question_id");

DROP INDEX IF EXISTS "tests_academic_question_test_id_3d95f0ee";
CREATE INDEX "tests_academic_question_test_id_3d95f0ee" ON "tests_academic_question" ("test_id");

DROP INDEX IF EXISTS "tests_academic_result_student_id_4dc57c31";
CREATE INDEX "tests_academic_result_student_id_4dc57c31" ON "tests_academic_result" ("student_id");

DROP INDEX IF EXISTS "tests_academic_result_test_id_486be42b";
CREATE INDEX "tests_academic_result_test_id_486be42b" ON "tests_academic_result" ("test_id");

DROP INDEX IF EXISTS "tests_academic_studentanswer_answer_id_66b4a286";
CREATE INDEX "tests_academic_studentanswer_answer_id_66b4a286" ON "tests_academic_studentanswer" ("answer_id");

DROP INDEX IF EXISTS "tests_academic_studentanswer_question_id_ef6a647b";
CREATE INDEX "tests_academic_studentanswer_question_id_ef6a647b" ON "tests_academic_studentanswer" ("question_id");

DROP INDEX IF EXISTS "tests_academic_studentanswer_result_id_c4333200";
CREATE INDEX "tests_academic_studentanswer_result_id_c4333200" ON "tests_academic_studentanswer" ("result_id");

DROP INDEX IF EXISTS "tests_academic_studentanswer_student_id_bb2ea4e0";
CREATE INDEX "tests_academic_studentanswer_student_id_bb2ea4e0" ON "tests_academic_studentanswer" ("student_id");

DROP INDEX IF EXISTS "tests_academic_test_course_id_283fc364";
CREATE INDEX "tests_academic_test_course_id_283fc364" ON "tests_academic_test" ("course_id");

DROP INDEX IF EXISTS "tests_academic_test_created_by_id_26bade48";
CREATE INDEX "tests_academic_test_created_by_id_26bade48" ON "tests_academic_test" ("created_by_id");

DROP INDEX IF EXISTS "tracking_progress_student_id_53c4c5d3";
CREATE INDEX "tracking_progress_student_id_53c4c5d3" ON "tracking_progress" ("student_id");

DROP INDEX IF EXISTS "users_usuario_groups_group_id_9d969afd";
CREATE INDEX "users_usuario_groups_group_id_9d969afd" ON "users_usuario_groups" ("group_id");

DROP INDEX IF EXISTS "users_usuario_groups_usuario_id_3a8a9a06";
CREATE INDEX "users_usuario_groups_usuario_id_3a8a9a06" ON "users_usuario_groups" ("usuario_id");

DROP INDEX IF EXISTS "users_usuario_groups_usuario_id_group_id_db69fe93_uniq";
CREATE UNIQUE INDEX "users_usuario_groups_usuario_id_group_id_db69fe93_uniq" ON "users_usuario_groups" ("usuario_id", "group_id");

DROP INDEX IF EXISTS "users_usuario_user_permissions_permission_id_bf5f5453";
CREATE INDEX "users_usuario_user_permissions_permission_id_bf5f5453" ON "users_usuario_user_permissions" ("permission_id");

DROP INDEX IF EXISTS "users_usuario_user_permissions_usuario_id_75526fda";
CREATE INDEX "users_usuario_user_permissions_usuario_id_75526fda" ON "users_usuario_user_permissions" ("usuario_id");

DROP INDEX IF EXISTS "users_usuario_user_permissions_usuario_id_permission_id_9b373975_uniq";
CREATE UNIQUE INDEX "users_usuario_user_permissions_usuario_id_permission_id_9b373975_uniq" ON "users_usuario_user_permissions" ("usuario_id", "permission_id");

COMMIT;
PRAGMA foreign_keys=ON;

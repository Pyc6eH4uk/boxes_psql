DROP TABLE IF EXISTS box_things;
DROP TABLE IF EXISTS boxes;
DROP TABLE IF EXISTS box_users;
CREATE TABLE box_users(
  user_id SERIAL PRIMARY KEY,
  user_login VARCHAR(256) NOT NULL UNIQUE,
  user_password TEXT NOT NULL
);
CREATE TABLE boxes(
  box_id SERIAL PRIMARY KEY,
  box_name VARCHAR(100) NOT NULL UNIQUE,
  box_color VARCHAR(20) NOT NULL,
  user_id INTEGER REFERENCES box_users(user_id)
);
CREATE TABLE box_things(
  thing_id SERIAL PRIMARY KEY,
  thing_name TEXT NOT NULL,
  box_id INTEGER REFERENCES boxes(box_id)
);
INSERT INTO box_users(user_login, user_password) VALUES('Ruslan', '12345');
INSERT INTO box_users(user_login, user_password) VALUES('Ruslan1', '12345');
DROP TABLE IF EXISTS SaaChats;

CREATE TABLE SaaChats (
    username VARCHAR(100) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    content TEXT NOT NULL,
    role VARCHAR(50) NOT NULL,
    PRIMARY KEY (username, timestamp),
	FOREIGN KEY (username) REFERENCES users(username)
);

DROP TABLE IF EXISTS Categories;

CREATE TABLE Categories (
    username VARCHAR(50) NOT NULL,
    category_id int NOT NULL,
	category_name VARCHAR(50) NOT NULL,
    category_description TEXT NOT NULL,
    weightage INT NOT NULL,
    payload JSON,
    PRIMARY KEY (username, category_id),
    FOREIGN KEY (username) REFERENCES users(username)
);

-- Insert into table Categories
INSERT INTO Categories (username, category_id, category_name, category_description, weightage, payload) VALUES
('louis', 1, 'Hobbies and Interests', 'Discover their passions and leisure activities', 10, '{}'),
('louis', 5, 'Expectations', 'Explore what they envision for relationships and life goals', 10, '{}'),
('louis', 2, 'Core Values', 'Uncover the principles that guide their decisions and actions', 10, '{}'),
('louis', 3, 'Thought-provoking', 'Challenge their perspectives with questions that stimulate deep thinking', 10, '{}'),
('louis', 4, 'Childhood, Family', 'Learn about their upbringing and family influences', 10, '{}'),
('louis', 6, 'Travel', 'Understand their experiences and aspirations related to travel', 10, '{}'),
('louis', 7, 'Friends and Social Life', 'Gain insight into their social dynamics and preferences', 10, '{}'),
('louis', 8, 'Career', 'Discuss their professional aspirations and work-life balance', 10, '{}'),
('louis', 9, 'Self-reflection', 'Engage in conversations about personal growth and self-awareness', 10, '{}'),
('louis', 10, 'Books, Movies & Games', 'Share and discuss their tastes in media and entertainment', 10, '{}'),
('louis', 11, 'Likes, Dislikes, and Pet Peeves', 'Identify their personal preferences and quirks', 10, '{}');

select * from Categories;

select * from SaaChats;

select * 
from Categories as c
where c.username = 'louis';



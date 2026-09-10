CREATE TABLE IF NOT EXISTS comments (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  game_slug TEXT NOT NULL,
  display_name TEXT NOT NULL,
  email TEXT,
  body TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected', 'hidden')),
  ip_hash TEXT,
  created_at TEXT NOT NULL,
  moderated_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_comments_game_status_created
ON comments (game_slug, status, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_comments_status_created
ON comments (status, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_comments_ip_created
ON comments (ip_hash, created_at DESC);

import psycopg2
con = psycopg2.connect(
    host = "ep-aged-rain-a472d7qt-pooler.us-east-1.aws.neon.tech",
    user = "default",
    password = "2pVZitHFc5aY",
    database = "verceldb"
    )
print(con)
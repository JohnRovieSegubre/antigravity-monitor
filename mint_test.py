import os, time, pymacaroons, sqlite3
s = os.getenv('MINT_SECRET')
m = pymacaroons.Macaroon(location='sovereign', identifier=str(int(time.time())), key=s)
conn = sqlite3.connect('data/sovereign.db')
c = conn.cursor()
c.execute('INSERT INTO sessions (identifier, balance_sats) VALUES (?, ?)', (m.identifier, 5000))
conn.commit()
print('MACAROON=' + m.serialize())

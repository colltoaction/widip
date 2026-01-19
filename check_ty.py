from discopy import closed
t = closed.Ty("")
print(f"Length of Ty(''): {len(t)}")
print(f"Is it empty? {t == closed.Ty()}")
print(f"Length of Ty(): {len(closed.Ty())}")

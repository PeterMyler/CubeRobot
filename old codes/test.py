s = "tat ehm niseahtfd  outnrl fe.t"
s = "at the mineshaft do turn left."
for i in range(len(s)):
    if i%2 == 0:
        print(end=s[i+1])
    else:
        print(end=s[i-1])
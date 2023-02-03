
% Rules

tens -> ten digit
tens -> ten
tens -> teen

num2 -> tens
num2 -> digit

tail2 -> num2
tail2 -> and num2

hundreds -> digit hundred
hundreds -> digit hundred tail2
ne-hundreds -> a hundred
ne-hundreds -> a hundred tail2
ne-hundreds -> tens hundred
ne-hundreds -> tens hundred tail2

num3 -> hundreds
num3 -> num2

tail3 -> num3
tail3 -> and num3

thousands -> num3 thousand
thousands -> num3 thousand tail3
ne-thousands -> a thousand
ne-thousands -> a thousand tail3

num5 -> thousands
num5 -> num3

tail5 -> num5
tail5 -> and num5

millions -> num3 million
millions -> num3 million tail5
ne-millions -> a million
ne-millions -> a million tail5

num8 -> millions
num8 -> num5

tail8 -> num8
tail8 -> and num8

billions -> num3 billion
billions -> num3 billion tail8
ne-billions -> a billion
ne-billions -> a billion tail8

num11 -> billions
num11 -> num8

tail11 -> num11
tail11 -> and num11

trillions -> num3 trillion
trillions -> num3 trillion tail11
ne-trillions -> a trillion
ne-trillions -> a trillion tail11

num[pl] -> zero
num[F] -> digit[F]
num[pl] -> tens
num[pl] -> hundreds
num[pl] -> ne-hundreds
num[pl] -> thousands
num[pl] -> ne-thousands
num[pl] -> millions
num[pl] -> ne-millions
num[pl] -> billions
num[pl] -> ne-billions
num[pl] -> trillions
num[pl] -> ne-trillions



all: client-rate.png client-sent.png server-rate.png

client-rate.png: client-rate.gp client-stats.csv
	gnuplot $<

client-sent.png: client-sent.gp client-stats.csv
	gnuplot $<

server-rate.png: server-rate.gp server-stats.csv
	gnuplot $<

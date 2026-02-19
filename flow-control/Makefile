PNG := client-rate.pdf client-sent.pdf server-rate.pdf

all: $(PNG)

client-rate.pdf: client-rate.gp client-stats.csv
	gnuplot $<

client-sent.pdf: client-sent.gp client-stats.csv
	gnuplot $<

server-rate.pdf: server-rate.gp server-stats.csv
	gnuplot $<


clean:
	rm -f $(PNG)

set datafile separator ","

set xlabel "time (s)"
set ylabel "rate (kB/s, log10)"
set logscale y
set format y "10^{%L}"
set key top right

set terminal pngcairo size 1280,500 enhanced font 'Ubuntu,16'
set output "server-rate.png"
plot "server-stats.csv" using 1:($2/1000) with lines lw 3 title "CA", \
     "server-stats.csv" using 1:($3/1000) with lines lw 3 title "SMA", \
     "server-stats.csv" using 1:($4/1000) with lines lw 3 title "EMA"

set terminal pdfcairo size 12.8, 5.0 enhanced font 'Ubuntu,16'
set output "server-rate.pdf"
replot

set output

set datafile separator ","
set logscale y
set format y "10^{%L}"

# set mytics 10
# set grid xtics ytics mytics
# set grid lw 1 lc rgb "gray30", lw 0.5 lc rgb "gray90"

set xlabel "time (s)"
set ylabel "rate (kB/s)"
# set yrange [0:1400]
unset key

set terminal pngcairo size 1280,500 enhanced font 'Ubuntu,16'
set output "client-rate.png"
plot "client-stats.csv" using 1:($3/1000) with lines lw 3 title "data"

set terminal pdfcairo size 12.8, 5.0 enhanced font 'Ubuntu,16'
set output "client-rate.pdf"
replot

set output

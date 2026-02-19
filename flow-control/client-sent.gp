set datafile separator ","

set xlabel "time (s)"
set ylabel "data (MB)"
set format y "%.1s"
unset key

set terminal pngcairo size 1280,500 enhanced font 'Ubuntu,16'
set output "client-sent.png"
plot "client-stats.csv" using 1:2 with lines lw 3 title "data"

set terminal pdfcairo size 12.8, 5.0 enhanced font 'Ubuntu,16'
set output "client-sent.pdf"
replot

set output

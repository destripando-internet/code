set datafile separator ","


set datafile separator ","
set terminal pngcairo size 1280,720 enhanced font 'Arial,12'
set output "sent.png"

set xlabel "time (s)"
set ylabel "data (MB)"
set format y "%.1s"
unset key
plot "stats.csv" using 1:2 with lines title "data"

import numpy as np
import matplotlib
matplotlib.use('WXAgg')
import pylab as pl
import time
import equipment.LabJack.u3 as u3

lj = u3.U3()

N = 100
REFRESH_MS = 100
CLOCK_PER_MS = 4000 # clock is 4MHz

try:

    lj.configIO(EnableCounter0=True, EnableCounter1=True, NumberOfTimersEnabled = 2, TimerCounterPinOffset=6, FIOAnalog=0x0F)
    #timer 0 on FIO6
    #timer 1 on FIO7
    #counter0 on EIO0
    #counter1 on EIO2
    lj.getFeedback(u3.TimerConfig(timer = 0, TimerMode = 10)) # system timer LSW
    lj.getFeedback(u3.TimerConfig(timer = 1, TimerMode = 11)) # system timer MSW

    feedback_req = [
        u3.Timer(timer=0, UpdateReset = False, Value = 0, Mode = None),
        u3.Timer(timer=1, UpdateReset = False, Value = 0, Mode = None),
        u3.Counter(counter = 0, Reset=True),
        u3.Counter(counter = 1, Reset=False)
        ]
    
    fig = pl.figure(1)
    ax  = fig.add_subplot(111)
    
    ax.set_xlabel("time (ms)")
    ax.set_ylabel("Counts (Hz)")
    
    T  = np.zeros(N, dtype=np.uint64) # clock times
    C0 = np.zeros(N, dtype=np.uint32) # raw counts between measurements
    C0_rate = np.zeros(N, dtype=np.float) # rate in Hz

    
    c0 = 0
    c1 = 0
    t  = 0 # in clock ticks
    t_prev = -1*REFRESH_MS*CLOCK_PER_MS # in clock ticks
    
    ii = 0
    
    plot_line, = ax.plot(np.arange(0,N)*REFRESH_MS, C0_rate)
    plot_current_pos = ax.axvline(ii)


    def update_graph(ax):
        global T, C0, ii, t, t_prev
    
        ii += 1
        ii %= N
    
        tLSW, tMSW, c0, c1 = lj.getFeedback(feedback_req)
        
        #t = tMSW << 32 + tLSW
        t_prev = t
        t = tLSW
        
        dt = np.abs(t - t_prev) #% 0xFFFF

        #c0_rate = c0*1e3/REFRESH_MS
        c0_rate = c0 * CLOCK_PER_MS * 1.0e3 / dt  # Hz
        
        #T[ii] = t
        C0[ii] = c0
        C0_rate[ii] = c0_rate
    
    
        plot_line.set_ydata(C0_rate)
        plot_current_pos.set_xdata( (ii*REFRESH_MS,ii*REFRESH_MS) )
        #self.hist_i += 1
        #self.hist_i %= HIST_LEN

        ax.set_title("%i, %i, %e, dt=%g ms (%i ticks)" % (t, c0, c0_rate, dt*1.0/CLOCK_PER_MS, dt))
        
        if (ii % 10) == 0:
            ax.relim()
            ax.autoscale_view(scalex=False, scaley=True)
            
        fig.canvas.draw()

    timer = fig.canvas.new_timer(interval=REFRESH_MS)
    #timer.set_interval(REFRESH_MS)
    #._timer_set_interval(REFRESH_MS)
    timer.add_callback(update_graph, ax)
    timer.start()
    
    pl.show()

finally:
    lj.close()
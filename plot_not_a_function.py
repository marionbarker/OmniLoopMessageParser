# This cell prepares the plot for the number of commands per sequence vs time

# Plot the number of commands in each sequence vs time since pod was paired
#fig = plt.figure(figsize=(10,5))
fig, ax = plt.subplots(figsize=(10,5))
ax.grid(color='lightgray', linestyle='-', linewidth=1)
# Tweak spacing to prevent clipping of ylabel
fig.tight_layout()
ax = plt.subplot2grid((1, 1), (0, 0))
ax.plot(times, lengths, marker='d', linestyle='None', alpha=0.3, c='b', markersize=6)
ax.set_xlabel('pod hrs')
ax.set_ylabel('Number Send/Recv in Sequence')
plt.grid()
ax.plot(singleton_times, singleton_ones, marker='o', linestyle='None', alpha=0.3, c='r', markersize=6)
ax.set_xlim(0, 80)
ax.set_ylim(0, max(lengths)+2)
ax.set_title(thisFile)


plt.show()

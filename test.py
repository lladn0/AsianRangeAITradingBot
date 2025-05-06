import plotly.graph_objects as go

fig = go.Figure(data=go.Bar(y=[2, 3, 1]))
fig.write_image("test.png", engine="kaleido")
print("✅ Image saved")
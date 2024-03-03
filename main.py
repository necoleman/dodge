import pyglet

from game_state import GameState

window = pyglet.window.Window(fullscreen=True)
batch = pyglet.graphics.Batch()


game_state = GameState(max_x=window.width, max_y=window.height, batch=batch)



@window.event 
def on_mouse_motion(x, y, dx, dy):
    game_state.point_to(x, y)


@window.event 
def on_mouse_drag(x, y, dx, dy, button, modifiers):
    game_state.ship.start_accel()
    game_state.point_to(x, y)


@window.event
def on_mouse_press(x, y, button, modifiers):
    game_state.ship.start_accel()
    game_state.point_to(x, y)
    

@window.event
def on_mouse_release(x, y, button, modifiers):
    game_state.ship.stop_accel()
    game_state.point_to(x, y)


@window.event
def on_draw():
    window.clear()
    batch.draw()






pyglet.clock.schedule_interval(game_state.update, 1/120.0)
pyglet.app.run()
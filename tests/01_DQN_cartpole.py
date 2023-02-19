# %%
import gymnasium as gym
import torch
import numpy as np
from collections import deque
from src.utils.util import ShellColor as sc

print(f"{sc.COLOR_PURPLE}Gym version:{sc.ENDC} {gym.__version__}")
print(f"{sc.COLOR_PURPLE}Pytorch version:{sc.ENDC} {torch.__version__}")

from src.agents.dqn_agent import DQNAgent
from src.utils import util as rl_util

#%%
# env = gym.make("CartPole-v1", render_mode="human")

env_name = "CartPole-v1"
env = gym.make(env_name)
rl_util.print_env_info(env=env)
env.observation_space.shape
# %%
config = rl_util.create_config()
config["batch_size"] = 32
config["buffer_size"] = 30000
config["gamma"] = 0.99
config["update_frequency"] = 4
config["lr"] = 0.001

agent = DQNAgent(
    obs_space_shape=env.observation_space.shape,
    action_space_dims=env.action_space.n,
    is_atari=False,
    config=config,
)

print(agent.config)
print(type(agent.memory))
#%%
save_dir = "result/DQN/cartpole/"
rl_util.create_directory(save_dir)
current_time = rl_util.get_current_time_string()
save_model_name = save_dir + env_name + "_" + current_time + ".pt"

# %%
rewards = deque([], maxlen=5)
total_rewards = []
losses = []
time_step = 0
epsilon = agent.config.epsilon_start
for i_episode in range(agent.config.n_episodes):
    obs, info = env.reset()
    avg_loss = 0
    len_game_progress = 0
    test_reward = 0
    while True:
        # env.render()
        action = agent.select_action(obs, epsilon)
        next_obs, reward, terminated, truncated, info = env.step(action)
        test_reward += reward
        done = terminated or truncated
        agent.store_transition(obs, action, reward, next_obs, done)

        if len(agent.memory.replay_buffer) > 1000:
            avg_loss += agent.update()
            agent.soft_update_target_network()
            # avg_loss += agent.loss

        obs = next_obs
        len_game_progress += 1
        if done:
            break

    epsilon = max(agent.config.epsilon_end, epsilon - agent.epsilon_decay)
    avg_loss /= len_game_progress

    if (i_episode) % 20 == 0:

        # test_reward = evaluate_agent(agent.q_predict)
        print(
            f"episode: {i_episode} | cur_reward: {test_reward:.4f} | loss: {avg_loss:.4f} | epsilon: {epsilon:.4f}"
        )
        rewards.append(test_reward)
        total_rewards.append(test_reward)
        losses.append(avg_loss)

    mean_rewards = np.mean(rewards)
    if mean_rewards > 490:
        current_time = rl_util.get_current_time_string()
        save_model_name = save_dir + "checkpoint_" + current_time + ".pt"
        print(f"Save model {save_model_name} | episode is {(i_episode)}")
        torch.save(agent.policy_network.state_dict(), save_model_name)
        break
    time_step += 1
env.close()

#%%

fig, ax = rl_util.init_2d_figure("Reward")
rl_util.plot_graph(
    ax,
    total_rewards,
    title="reward",
    ylabel="reward",
    save_dir_name=save_dir,
    is_save=True,
)
rl_util.show_figure()
fig, ax = rl_util.init_2d_figure("Loss")
rl_util.plot_graph(
    ax, losses, title="loss", ylabel="loss", save_dir_name=save_dir, is_save=True
)
rl_util.show_figure()


# %%
# load the weights from file
env = gym.make("CartPole-v1", render_mode="human")
for ep in range(10):
    observation, _ = env.reset()
    total_reward = 0
    while True:
        env.render()
        state = torch.tensor(observation, dtype=torch.float, device=agent.config.device)
        action = torch.argmax(agent.policy_network(state)).item()
        next_obs, reward, terminated, truncated, info = env.step(action)
        done = terminated or truncated
        total_reward += reward
        observation = next_obs
        if done:
            break
    print(total_reward)
env.close()

#%%
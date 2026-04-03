from env.environment import EmailEnv

env = EmailEnv()

obs = env.reset()

done = False

while not done:

   
    print("\nEMAIL:")
    print(obs)

    print("\nAvailable actions:")
    print("delete_email | archive_email | mark_important")

    action = input("Enter action: ")

    obs, reward, done, info = env.step(action)

    print("Reward:", reward)

print("\nEpisode finished.")
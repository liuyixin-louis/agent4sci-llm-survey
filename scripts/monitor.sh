# #!/usr/bin/env bash
time_counter=0

messages_pool=(
    "Please judge yourself on the progress based on task master list and progress. And keep going with the next if you did not encouter something challenging; when encountering something tricky please pause and make ultra think on what is the potential adjustment to make to resolve or bypass the challenge toward the end target. "
    # If the boss is not satisfied, please make some reasoning on what could be improved. 
    # "Good progress. keep going. "
    # "Are you on track on the task? "
    # "Bad progress. Please do some rethinking on your current stage. At the end we just need the table of results for paper. "
)

supervisor_message_pool=(
    "Please make evaluation on the current progress based on the task master stauts and also the codebase and paper writing; give feedback and guidance to ./docs/feedback.md"
)

name=ccw

while true; do 
    if [ $time_counter -eq 30 ]; then
        tmux send-keys -t $name:0.0 -l 'Please summarize your progress so far, highlighting the achievements and challenges you have faced and make potential adjustment to meet the goal of submission. Keep moving to the next task if you done with the current task. For scripts to run, please run yourself, we have time. please output your progress report to ./docs/progress-report/*.md with timestamp; Do some scripts cleaning regularly too, make sure those oneoff things are cleaned up and the reorganization of code be documented. ' \; run-shell 'sleep 0.5' \; send-keys -t $name:0.0 Enter      
        time_counter=0
    else
        random_message=${messages_pool[$RANDOM % ${#messages_pool[@]}]}
        tmux send-keys -t $name:0.0 -l "$random_message" \; run-shell 'sleep 0.51' \; send-keys -t $name:0.0 Enter      
        time_counter=$((time_counter + 1))
    fi
    sleep 180
done
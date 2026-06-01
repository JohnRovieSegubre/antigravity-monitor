echo y | gcloud compute scp --recurse landing\blogs rovie_segubre@instance-20260208-234621:/home/rovie_segubre/sovereign/landing/ --project=super-ai-483717 --zone=us-central1-c --tunnel-through-iap
echo y | gcloud compute ssh rovie_segubre@instance-20260208-234621 --project=super-ai-483717 --zone=us-central1-c --tunnel-through-iap --command="chmod -R 755 ~/sovereign/landing/blogs/"

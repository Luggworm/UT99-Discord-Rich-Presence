class UT99PresenceMutator extends Mutator;

function PostBeginPlay()
{
    Super.PostBeginPlay();
    Spawn(class'UT99PresenceLink');
}

defaultproperties
{
    FriendlyName="UT99 Discord Presence Bridge"
    Description="Reports local match details to a localhost companion app."
}

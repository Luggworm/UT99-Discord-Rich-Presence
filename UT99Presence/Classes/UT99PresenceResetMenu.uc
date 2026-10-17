class UT99PresenceResetMenu extends UMenuModMenuItem;

function Execute()
{
    local PlayerPawn P;
    Log("UT99Presence: Reset menu clicked");
    if (MenuItem == None || MenuItem.Owner == None || MenuItem.Owner.Root == None)
    {
        Log("UT99Presence: Reset menu has no owner/root");
        return;
    }
    P = MenuItem.Owner.Root.GetPlayerOwner();
    if (P == None)
    {
        Log("UT99Presence: Reset menu could not find player");
        return;
    }
    P.Spawn(class'UT99PresenceResetLink');
    P.ClientMessage("Discord Presence reset requested.");
}

defaultproperties
{
    MenuCaption="Reset Discord Presence"
    MenuHelp="Clear campaign status without restarting UT99"
}

import jenkins.model.*
import hudson.security.*

def instance = Jenkins.getInstance()

def realm = instance.getSecurityRealm()
if (realm == null || realm instanceof HudsonPrivateSecurityRealm == false) {
    def hudsonRealm = new HudsonPrivateSecurityRealm(false)
    hudsonRealm.createAccount("admin", "admin123")
    instance.setSecurityRealm(hudsonRealm)

    def strategy = new FullControlOnceLoggedInAuthorizationStrategy()
    strategy.setAllowAnonymousRead(false)
    instance.setAuthorizationStrategy(strategy)
    instance.save()
    println "--> Jenkins security initialized: created user 'admin' (password: 'admin123')"
}

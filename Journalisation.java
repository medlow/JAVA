// Classe basée sur le pattern Singleton qui permet la journalisation de l'application.
public class Journalisation {
        private static Journalisation uniqueInstance;// Stockage de l'unique instance de cette classe.
        private String log;// Chaine de caractères représentant les messages de log.

        // Constructeur en privé (donc inaccessible à l'extérieur de la classe).
        private Journalisation() {
                log = new String();
        }

        // Méthode statique qui sert de pseudo-constructeur (utilisation du mot clef
        // "synchronized" pour le multithread).
        public static synchronized Journalisation getInstance() {
                if (uniqueInstance == null) {
                        uniqueInstance = new Journalisation();
                }
                return uniqueInstance;
        }

        // Méthode qui permet d'ajouter un message de log.
        public void ajouterLog(String log) {
                // On ajoute également la date du message.
                Date d = new Date();
                DateFormat dateFormat = new SimpleDateFormat("dd/MM/yy HH'h'mm");
                this.log += "[" + dateFormat.format(d) + "] " + log + "\n";
        }

        // Méthode qui retourne tous les messages de log.
        public String afficherLog() {
                return log;
        }
}
# Textual and graphical languages for modern domain tools

Complex domains rarely fit neatly into a single user interface.

Some information is most precise and efficient when expressed as text. Other information becomes much easier to understand when you can see structures, dependencies, and relationships as a diagram. For many domain-specific tools, the best answer is therefore not **text or graphics**, but a thoughtful combination of both.

The challenge is building that combination without creating two separate systems that become expensive to develop and maintain.

Modern language engineering frameworks make a different approach possible: one underlying model can power rich textual editing, synchronized diagrams, and a custom development environment around them. And the same application can run in the browser, on the desktop, or both.

## Text and diagrams can serve the same domain

Consider a state machine.

You might describe its states and transitions with a concise textual language. The editor can understand that language, validate it, offer completion, and help users navigate through the model.

At the same time, a diagram can visualize those exact states and transitions. Instead of maintaining a separate drawing, the graphical representation is generated directly from the textual model.

That gives users two ways to understand the same information.

The textual language remains the primary representation, while the diagram provides another perspective on its structure. When the text changes, the visualization follows. When users explore the diagram, elements can be linked back to their source. This is the approach we use with Eclipse Langium for language engineering and Eclipse Sprotty for web-native diagrams.

For a domain-specific application, that distinction matters. You are not adding a diagram as decoration. You are creating another interface to the same domain knowledge.

## The architecture behind the user experience matters

A polished interface is only one side of a successful tool.

The technology underneath it determines how easily the product can be developed, deployed, extended, and maintained over many years.

This was one of our motivations for creating Langium.

Before Langium, we had already built browser-based language tools by combining Eclipse Xtext, Sprotty, and Eclipse Theia. Functionally, this architecture worked well: Xtext provided the textual language tooling, Sprotty the diagrams, and Theia the web-based development environment.

But there was an important architectural mismatch.

Xtext is based on Java, while Sprotty and Theia belong to the TypeScript and web ecosystem. Although the individual components could communicate through established protocols, the development environment effectively consisted of two technology stacks with different runtimes, build systems, dependency management, and developer tooling.

That complexity does not necessarily show up in a product demo. It does show up over the lifetime of the product: during onboarding, development, testing, upgrades, and maintenance.

For organizations investing in a domain-specific tool, this is an important part of the technology decision. The question is not only whether an architecture can implement today's requirements. It is whether your team will still want to work with it several years from now.

## One technology stack makes a difference

We created Langium to bring language engineering into the TypeScript ecosystem.

It takes concepts we had already applied successfully with Xtext and provides them on a foundation designed for modern web applications and IDEs. Languages are defined with a grammar, references between model elements are resolved by the framework, and the resulting domain model is represented using regular TypeScript types.

For projects that combine a DSL with Sprotty diagrams and a web-based IDE, that means the central pieces can share one technology stack.

The result is much more than architectural neatness.

The code can be built, tested, and packaged with a consistent toolchain. Developers joining the project do not need to switch constantly between unrelated ecosystems. And the application can integrate naturally with the technologies already used for modern browser-based interfaces. The original Langium and Sprotty architecture was designed specifically to reduce that engineering friction and improve long-term maintainability.

Langium has since become an established part of our language engineering stack and integrates naturally with VS Code, Eclipse Theia, and custom web applications.

## From language to complete domain tool

A domain-specific language rarely lives in isolation.

The language may be the foundation, but users experience the complete application around it: editors, diagrams, navigation, validation, dedicated views, dashboards, and workflows.

That is why we see language engineering and custom IDE development as closely connected disciplines.

A Langium language server can provide the understanding of the domain model. Sprotty can turn structures and relationships from that model into interactive graphical views. VS Code or Eclipse Theia can provide the surrounding development environment. The same language services can also be integrated into a more focused web application when a full IDE would be unnecessary.

This gives product teams considerable freedom in designing the user experience.

Developers might work with the language in a familiar IDE. Domain experts might interact mainly through specialized views. Diagrams can make complex structures easier to explore, while the textual representation provides the underlying model from which other artifacts can be generated.

The important part is that these interfaces do not have to become separate products with separate implementations.

They can be different windows into the same domain.

## Cloud or desktop does not have to be a fundamental choice

Another advantage of web technology is that the deployment model becomes much more flexible.

An application built for the browser can naturally be deployed as a cloud-based tool. The same technology can also form the foundation of a desktop application. Eclipse Theia, for example, is explicitly designed for custom development environments that run in the cloud, on the desktop, or both.

That flexibility can be valuable when a product needs to serve different environments.

One customer may require a browser-based deployment integrated into an existing platform. Another may need a self-contained desktop application. A product may start in one environment and expand into another later.

A coherent architecture makes these scenarios easier to support without reinventing the core language and visualization tooling each time.

## Text-first or graphics-first?

There is no universal answer to how a domain should be represented.

In the architecture described here, the textual language is the primary representation. The diagram is derived from it and gives users an additional way to explore the model.

For many systems, that is an excellent fit.

But some domains are inherently graphical. If creating and manipulating diagrams is the primary way users express information, a graphics-first architecture may be more appropriate. Eclipse GLSP extends the same web-based diagramming foundations toward fully graphical editing.

The important decision is therefore not whether textual languages are better than graphical ones.

It is **which representation should carry the model, which interactions your users need, and how the different views should work together**.

Once those questions are answered, the technology should support that design rather than dictate it.

## Build the tool around the domain

Good domain tools hide a lot of engineering behind an interface that feels natural to its users.

Sometimes that interface is primarily textual. Sometimes it is graphical. Often, the strongest solution combines both.

What should remain invisible is unnecessary architectural complexity.

That was a major motivation behind Langium and its integration with tools such as Sprotty, VS Code, and Eclipse Theia: giving teams a coherent foundation for language-aware applications that can combine text, diagrams, and custom workflows without stitching together unrelated technology stacks.

At TypeFox, we work on both sides of that equation. We build the open source frameworks, and we use them to create custom domain tools for our customers.

If your domain needs its own language, visual representation, or development environment, we can help find the architecture that fits.
